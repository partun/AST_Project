from lib.Extractor import extract_bug_pattern


def main() -> None:
    print('running main')
    extract_bug_pattern(
        'jonas/tig_8c11094f0b8ae9b82b1a3c44e6588e496214866b')
    # 'videolan/vlc_d2ef799a6f922bcfc59aea23eafc546be0d31fb0')


if __name__ == '__main__':
    main()
