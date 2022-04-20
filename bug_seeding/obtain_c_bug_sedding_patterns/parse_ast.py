from clang.cindex import Index
from pprint import pprint

MAX_DEPTH = 10


def get_cursor_id(cursor, cursor_list=[]):
    if cursor is None:
        return None

    # FIXME: This is really slow. It would be nice if the index API exposed
    # something that let us hash cursors.
    for i, c in enumerate(cursor_list):
        if cursor == c:
            return i
    cursor_list.append(cursor)
    return len(cursor_list) - 1


def get_info(node, depth=0):
    if depth >= MAX_DEPTH:
        children = None
    else:
        children = [get_info(c, depth+1)
                    for c in node.get_children()]
    return {'id': get_cursor_id(node),
            'kind': node.kind,
            'usr': node.get_usr(),
            'spelling': node.spelling,
            'location': node.location,
            'extent.start': node.extent.start,
            'extent.end': node.extent.end,
            'is_definition': node.is_definition(),
            'definition id': get_cursor_id(node.get_definition()),
            'children': children}


def parse_c_programm(path: str):

    index = Index.create()
    tu = index.parse(path)

    pprint(('nodes', get_info(tu.cursor)))


parse_c_programm(
    '/Users/dominic/eth/01_SS22/AST_AutomatedSoftwareTesting/Project/SemSeed/targets/__libpng-1.6.37/png.c')
