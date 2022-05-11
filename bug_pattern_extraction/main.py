from lib.Extractor import extract_bug_pattern


def main() -> None:
    print('running main')
    extract_bug_pattern(
        'libgit2/libgit2_f8821405773d76025a29563f7b263a2b9b558572')
    # 'videolan/vlc_d2ef799a6f922bcfc59aea23eafc546be0d31fb0')


if __name__ == '__main__':
    main()
