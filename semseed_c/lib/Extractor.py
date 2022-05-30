from unittest import result
from lib.BugFixes import MongoDB
from lib.CodeAnalysis import CodeAnalysis, SrcRange
import pygit2 as git
from pprint import pprint
from typing import Dict, Type, NamedTuple, Tuple, Optional, List, Any
from clang.cindex import Index, TranslationUnit, CursorKind, SourceLocation, SourceRange, TokenKind


def select_node(analysed_code: List[Dict[str, Any]], changed_line_no: int) -> Optional[Dict[str, Any]]:
    candidate_node: Optional[Dict[str, Any]] = None
    candidate_node_token_cnt = -1
    for node in analysed_code:
        src_range: SrcRange = node['range']
        if src_range.start_line == changed_line_no and src_range.is_one_line() and (token_cnt := len(node['tokens'])) > candidate_node_token_cnt:
            candidate_node = node
            candidate_node_token_cnt = token_cnt

    # Once, we have all the Nodes that belongs to the changed line. We select the Node that best expresses it.
    # Note: There is no guarantee that this is the correct Node. This is simply an approximation.
    return candidate_node


def rename_abstracted_changes(fixed_node: Dict[str, Any], buggy_node: Dict[str, Any]) -> Dict[str, Any]:
    """
    It is possible that both the fixed and the buggy part of the conditional test contains the
    same Identifiers. Since, we abstract the Identifiers independently, might need to be named properly.
    Eg.
     Buggy →
             a < b && c < d gets abstracted as Idf_1 < Idf_2 && Idf_3 < Idf_4
     Fixed →
             a < c && r < d gets abstracted as Idf_1 < Idf_2 && Idf_3 < Idf_4
    The proper renaming should be
    Idf_1 < Idf_3 && Idf_5 < Idf_4

    Although mentioned above with the example of a 'buggy' to 'fix' renaming. We
    actually do not rename the 'fix' part and rather rename the 'Idf_' of the
    'buggy' part.
    We do this since we want to learn how to seed bugs and not how to fix them
    """

    fixed_abstract_tokens = fixed_node['abstracted_tokens'].copy()
    buggy_abstract_tokens = buggy_node['abstracted_tokens'].copy()
    idf_map = dict()
    lit_map = dict()

    for token_type, token_value, abstract_token in zip(
        fixed_node['token_types'], fixed_node['tokens'], fixed_node['abstracted_tokens']
    ):
        if token_type == TokenKind.IDENTIFIER and token_value not in idf_map:
            idf_map[token_value] = abstract_token
        elif token_type == TokenKind.LITERAL and token_value not in lit_map:
            lit_map[token_value] = abstract_token

    for i, (token_type, token_value, abstract_token) in enumerate(zip(
        buggy_node['token_types'], buggy_node['tokens'], buggy_node['abstracted_tokens']
    )):
        if token_type == TokenKind.IDENTIFIER:
            buggy_abstract_tokens[i] = idf_map.setdefault(
                token_value, f'Idf_{len(idf_map) + 1}')

        elif token_type == TokenKind.LITERAL and token_value not in lit_map:
            buggy_abstract_tokens[i] = lit_map.setdefault(
                token_value, f'Lit_{len(lit_map) + 1}')

    return {
        'fix': fixed_abstract_tokens,
        'buggy': buggy_abstract_tokens,
        'idf_mapping': {abstract: concrete for concrete, abstract in idf_map.items()},
        'lit_mapping': {abstract: concrete for concrete, abstract in lit_map.items()}
    }


def extract_bug_pattern(commit_id: str) -> str:

    # get the commit from mongodb

    mongo = MongoDB()
    commit = mongo.get_commit(commit_id)
    if commit is None:
        print(f'cloud not find commit with id: {commit_id}')
        return 'cloud not find commit'

    for change in commit['single_line_changes']:
        change['analysis_report'] = 'Not Analysed'

        repo = git.Repository(f"{commit['local_repo_path']}")

        """
        fixed file
        """
        fixed_file = repo.revparse_single(
            f"{commit['commit_hash']}:{change['new_file']['path']}")
        fixed_extractor = Extractor.from_source(
            commit['local_repo_path'] + change['new_file']['path'],
            fixed_file.read_raw()
        )
        fixed_analysed_code = fixed_extractor.extract_specific_nodes()
        fixed_extractor.abstract_all_idf_and_lit(fixed_analysed_code)

        if len(fixed_analysed_code) == 0:
            # could not parse fixed file
            change['analysis_report'] = 'fixed_File_not_parsable'
            continue

        fixed_selected_node = select_node(
            fixed_analysed_code, change['new_file']['line_num'])
        if fixed_selected_node is None:
            change['analysis_report'] = 'fixed_Node_not_found'
            continue
        fixed_token_seq_of_changed_line = fixed_extractor.line_to_token_seqence[
            change['new_file']['line_num']]
        change['new_file']['identifiers'] = fixed_extractor.scope_to_idf
        change['new_file']['literals'] = fixed_extractor.scope_to_lit

        """
        buggy file
        """
        buggy_file = repo.revparse_single(
            f"{commit['parent_hash']}:{change['old_file']['path']}")
        buggy_extractor = Extractor.from_source(
            commit['local_repo_path'] + change['old_file']['path'],
            buggy_file.read_raw()
        )
        buggy_analysed_code = buggy_extractor.extract_specific_nodes()
        buggy_extractor.abstract_all_idf_and_lit(buggy_analysed_code)

        if len(buggy_analysed_code) == 0:
            # could not parse buggy file
            change['analysis_report'] = 'buggy_File_not_parsable'
            continue

        buggy_selected_node = select_node(
            buggy_analysed_code, change['old_file']['line_num'])
        if buggy_selected_node is None:
            change['analysis_report'] = 'buggy_Node_not_found'
            continue
        buggy_token_seq_of_changed_line = buggy_extractor.line_to_token_seqence[
            change['old_file']['line_num']]
        change['old_file']['identifiers'] = buggy_extractor.scope_to_idf
        change['old_file']['literals'] = buggy_extractor.scope_to_lit

        """
        Sometimes the selected Nodes are wrong and do not actually represent the change.
        There does not exist a single node that can capture the change
        Eg. https://github.com/axios/axios/commit/c573a12b748dd50456e27bbf1fd3e6561cb0b3d2
        https://github.com/strapi/strapi/commit/cc1669faf55ebd9b3029c4a03a7a5b06d8e5d71b
        """
        token_diff_in_commit = \
            len(fixed_token_seq_of_changed_line) - \
            len(buggy_token_seq_of_changed_line)
        token_diff_in_extraction = \
            len(fixed_selected_node['tokens']) - \
            len(buggy_selected_node['tokens'])
        if fixed_selected_node['tokens'] == buggy_selected_node['tokens'] or \
                token_diff_in_commit != token_diff_in_extraction:
            change['analysis_report'] = 'neither_Node_not_found'
            continue

        change['analysis_report'] = 'success'
        change['new_file']['change_analysis'] = fixed_selected_node
        change['old_file']['change_analysis'] = buggy_selected_node
        change['change_summary'] = rename_abstracted_changes(
            fixed_selected_node, buggy_selected_node)

    mongo.store_extracted_pattern(commit_id, commit['single_line_changes'])
    return change['analysis_report']


class Extractor(CodeAnalysis):
    def __init__(self, ast: TranslationUnit) -> None:
        super().__init__(ast)

    def find_token_index_from_range(self, src_range: SourceRange) -> Tuple[int, int]:
        start = None
        end = None

        range_iter = iter(enumerate(self.token_range_list))
        try:
            while True:
                i, r = next(range_iter)
                if src_range.encapsules(r):
                    start = i
                    while True:
                        end, r = next(range_iter)
                        if not src_range.encapsules(r):
                            return start, end
        except StopIteration:
            if start is None or end is None:
                raise ValueError()

            return start, end

    def extract_specific_nodes(self) -> List[Dict[str, Any]]:
        extracted_nodes = []

        def rec_traverse(node, parent_func_name, parent_func_range) -> None:
            start = node.extent.start
            end = node.extent.end
            src_range = SrcRange.form_source_range(node.extent)
            line = f'{start.line}-{end.line}'

            self.range_to_node_type[src_range] = str(node.kind)

            if node.kind == CursorKind.TRANSLATION_UNIT:
                func_name = f'__GLOBAL_{src_range}'
                self.func_name_stack[func_name] = src_range

                for child in node.get_children():
                    rec_traverse(child, func_name, src_range)
                return

            if node.kind == CursorKind.FUNCTION_DECL:
                func_name = node.spelling
                assert func_name
                self.func_name_stack[f'{func_name}_{src_range}'] = src_range

                for child in node.get_children():
                    rec_traverse(child, func_name, src_range)
                return

            if all((
                src_range.is_one_line(),
                self.is_literal(node.kind) is None,
                node.kind != CursorKind.DECL_REF_EXPR,
                node.kind != CursorKind.LABEL_REF
            )):

                try:
                    # start_index, end_index = self.find_token_index_from_range(
                    #     src_range)

                    # pprint(self.token_type_list[start_index:end_index])
                    extracted_data = {
                        'tokens': [t.spelling for t in node.get_tokens()],
                        'token_types': [t.kind for t in node.get_tokens()],

                        'range': src_range,
                        'type': node.kind,
                        'line': src_range.to_line_str(),
                        'parent_func': parent_func_name,
                        'parent_func_range': parent_func_range
                    }
                    extracted_nodes.append(extracted_data)
                except ValueError:
                    pass

            for child in node.get_children():
                rec_traverse(child, parent_func_name, parent_func_range)
            return

        rec_traverse(self.root_cursor, None, None)
        return extracted_nodes

    @staticmethod
    def abstract_all_idf_and_lit(analysed_code: List[Dict[str, Any]]):
        for extracted_node_data in analysed_code:
            Extractor.abstract_idf_and_lit(extracted_node_data)

    @staticmethod
    def abstract_idf_and_lit(extracted_node_data: Dict[str, Any]):
        idf_val_to_id = dict()
        idf_count = 0
        lit_val_to_id = dict()
        lit_count = 0

        abstracted_tokens = []
        for token_type, token in zip(extracted_node_data['token_types'], extracted_node_data['tokens']):
            if token_type == TokenKind.IDENTIFIER:
                abstract_token = idf_val_to_id.setdefault(
                    token, 'Idf_{}'.format(idf_count := idf_count + 1))
            elif token_type == TokenKind.LITERAL:
                abstract_token = lit_val_to_id.setdefault(
                    token, 'Lit_{}'.format(lit_count := lit_count + 1))
            else:
                abstract_token = token

            abstracted_tokens.append(abstract_token)

        extracted_node_data['abstracted_tokens'] = abstracted_tokens
