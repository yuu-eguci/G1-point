"""
Python やるときにいつもあって欲しい自分用モジュールです。
"""

# Built-in modules.
import os
import dotenv


# .env をロードします。
# 本スクリプトは .env がなくても動きます。(そのための raise_error_if_not_found です。)
# NOTE: raise_error_if_not_found=False .env が見つからなくてもエラーを起こさない。
dotenv.load_dotenv(dotenv.find_dotenv(raise_error_if_not_found=False))


def get_env(keyname: str) -> str:
    """環境変数を取得します。
    GitHub Actions では環境変数が設定されていなくても yaml 内で空文字列が入ってしまう。空欄チェックも行います。

    Arguments:
        keyname {str} -- 環境変数名。

    Raises:
        KeyError: 環境変数が見つからない。

    Returns:
        str -- 環境変数の値。
    """
    _ = os.environ[keyname]
    if not _:
        raise KeyError(f'{keyname} is empty.')
    return _


LINE_CHANNEL_ACCESS_TOKEN = get_env('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = get_env('LINE_CHANNEL_SECRET')

if __name__ == '__main__':
    print(repr(LINE_CHANNEL_ACCESS_TOKEN))
    print(repr(LINE_CHANNEL_SECRET))