"""netkeiba_scraper

netkeiba ウェブサイトからレース結果を取得するスクリプトです。
"""

# Third-party modules.
import requests
from bs4 import BeautifulSoup, element

# User modules.
import utils

# utils モジュール用のロガーを作成します。
logger = utils.get_my_logger(__name__)


def scrape(year: str, racetrack_code: str, times: str, date: str, race_number: str):

    # 引数チェックです。桁数をチェック。
    assert len(year) == 4, 'Argument "year" must be 4 characters.'
    assert len(racetrack_code) == 2, 'Argument "racetrack_code" must be 2 characters.'
    assert len(times) == 2, 'Argument "times" must be 2 characters.'
    assert len(date) == 2, 'Argument "date" must be 2 characters.'
    assert len(race_number) == 2, 'Argument "race_number" must be 2 characters.'

    # 対象の race_id を構築します。
    # NOTE: おそらく [西暦][競馬場コード][第何回][何日][何レース] のフォーマットだと予想されています。
    race_id = year + racetrack_code + times + date + race_number
    logger.debug(f'Run with race_id {race_id}')

    # Web ページを取得します。
    # NOTE: この URL は情報がなくとも 200 が返ります。
    #       情報のないページのときの対応は pick_payout_details の中で行っています。
    url = f'https://race.netkeiba.com/race/result.html?race_id={race_id}'
    logger.debug(f'Target page is {url}')
    response = requests.get(url)
    assert response.status_code == 200, f'Failed to get information of race_id={race_id}'

    # NOTE: このページには <meta charset="EUC-JP"> が設定されています。 encoding をそれに合わせます。
    response.encoding = response.apparent_encoding
    html_source = response.text

    # NOTE: テスト中に何度もスクレイピングをかけるのは気が引けるので、
    #       開発中はコレ使ってー。そして上の requests はコメントアウトを。
    # html_source = get_dummy_html_source()

    # 「払い戻し」情報を抽出します。
    # NOTE: これは、いつ構造が変わってもおかしくない html から情報を取得する処理です。
    #       予測せぬエラーに備え、結果のチェックを行っています。
    payout_information = pick_payout_details(html_source)

    assert payout_information['tansho_payout'] >= 0, 'tansho_payout is invalid.'
    assert payout_information['umaren_payout'] >= 0, 'umaren_payout is invalid.'
    assert payout_information['umatan_payout'] >= 0, 'umatan_payout is invalid.'
    assert payout_information['fuku3_payout'] >= 0, 'fuku3_payout is invalid.'
    assert payout_information['tan3_payout'] >= 0, 'tan3_payout is invalid.'
    assert payout_information['ranking1'] >= 0, 'ranking1 is invalid.'
    assert payout_information['ranking2'] >= 0, 'ranking2 is invalid.'
    assert payout_information['ranking3'] >= 0, 'ranking3 is invalid.'

    return payout_information


def get_dummy_html_source():
    """テスト中に何度もスクレイピングをかけるのは気が引けるので、
    ローカルに DL した html source を返します。
    """

    with open('./dummy2.html', 'r') as f:
        return f.read()


def pick_payout_details(html_source: str) -> dict:
    """html source から、抽出したい情報を取得して dict で返します。
    今回、 html から取得する情報が多く、
    ビジネスロジックが複雑になるので関数を分けています。

    必要なのは
    - 単勝の価格 --> tr.Tansho > td.Payout > span
    - 馬連の価格 --> tr.Umaren > td.Payout > span
    - 馬単の価格 --> tr.Umatan > td.Payout > span
    - 3連複の価格 --> tr.Fuku3 > td.Payout > span
    - 3連単の価格 --> tr.Tan3 > td.Payout > span
    - 順位 --> 複勝から取得 tr.Fukusho > td.Result > (複数の) div > span
    """

    soup = BeautifulSoup(html_source, 'lxml')

    # 適切な html source かどうかを確認します。
    assert soup.select_one('tr.Tansho > td.Payout > span') is not None, (
        'Can not get "Tansho" value.'
        ' HTML structure is not what we expect. or requested page does not have payout information.'
    )

    # 「単勝」の価格を取得します。
    tansho_payout = soup.select_one('tr.Tansho > td.Payout > span')
    # 「馬連」の価格を取得します。
    umaren_payout = soup.select_one('tr.Umaren > td.Payout > span')
    # 「馬単」の価格を取得します。
    umatan_payout = soup.select_one('tr.Umatan > td.Payout > span')
    # 「3連複」の価格を取得します。
    fuku3_payout = soup.select_one('tr.Fuku3 > td.Payout > span')
    # 「3連単」の価格を取得します。
    tan3_payout = soup.select_one('tr.Tan3 > td.Payout > span')

    # 金額は int が扱いやすいと思うので、 int にします。
    def foo(span: element.Tag) -> int:
        return int(span.get_text().replace(',', '').replace('円', ''))
    tansho_payout = foo(tansho_payout)
    umaren_payout = foo(umaren_payout)
    umatan_payout = foo(umatan_payout)
    fuku3_payout = foo(fuku3_payout)
    tan3_payout = foo(tan3_payout)

    # 順位を取得します。
    # tr.Fukusho > td.Result > (複数の) div > span
    ranking = []
    for div in soup.select('tr.Fukusho > td.Result > div'):
        horse_number = div.select_one('span').get_text()
        if horse_number:
            ranking.append(int(horse_number))

    return {
        'tansho_payout': tansho_payout,
        'umaren_payout': umaren_payout,
        'umatan_payout': umatan_payout,
        'fuku3_payout': fuku3_payout,
        'tan3_payout': tan3_payout,
        'ranking1': ranking[0] if len(ranking) >= 1 else -1,
        'ranking2': ranking[1] if len(ranking) >= 2 else -1,
        'ranking3': ranking[2] if len(ranking) >= 3 else -1,
    }


if __name__ == '__main__':
    payout_information = scrape(
        year='2021',
        racetrack_code='09',
        times='02',
        date='06',
        race_number='21',
    )
    logger.debug(payout_information)
