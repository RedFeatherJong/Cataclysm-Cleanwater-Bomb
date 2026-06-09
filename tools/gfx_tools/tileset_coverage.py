#!/usr/bin/env python3
"""
生成贴图贡献追踪表（中文表头 CSV）

将「游戏需要的全部贴图 ID」与「贴图包已有 ID」「overlay ID」做外连接，
聚合成每个游戏实体一行的表格，标记已有/缺失，并附带贡献协作所需的
空列（提交、贡献者、完成状态），供团队认领与填写。

用法（先用官方工具链生成三份 CSV）:

  cd Cataclysm-Cleanwater-Bomb

  python3 tools/json_tools/table.py -f csv --nonestring "" \\
   --tileset type id name description color looks_like "copy-from" longest_side \\
   > all_game_ids.csv

  python3 tools/json_tools/generate_overlay_ids.py > all_overlay_ids.csv

  # 注意：list_tileset_ids.py 读取的是 compose 之后的成品目录（含 tile_config.json）
  python3 tools/gfx_tools/list_tileset_ids.py <composed_tileset_dir> > tileset_ids.csv

  python3 tools/gfx_tools/tileset_coverage.py \\
   all_game_ids.csv all_overlay_ids.csv tileset_ids.csv \\
   tileset_coverage_output.csv

输出 CSV 列:
  类型, ID, 名称, 形似, 当前贴图, 完成状态, 提交, 贡献者, 备注

  当前贴图: 已有 / 形似回退 / 缺失
  完成状态: 已合并(已有贴图) / 待领取(缺失) —— 进行中 / 已完成 由贡献者手动更新
  提交:     留空，供贡献者填入图片链接（如 ![](url)）
  贡献者:   留空，供认领者填写
"""
import argparse
import re
import sys

from typing import Union

import pandas


REPLACEMENTS = (
    r'^overlay_(.+)_sees_player$',
)

DELETION_RE = (
    r'_season_(spring|summer|autumn|winter)|'
    r'^\[|'
    r'\]$|'
    r'^overlay(_(male|female))?_(effect|mutation|worn|wielded(_corpse)?)_|'
    r'^overlay_|'
    r'^corpse_|'
    r'^vp_|'
    r'(_('
    r'cover|cross|horizontal|horizontal_2|vertical|vertical_2|ne|nw|se|sw'
    r'))?'
    r'(_('
    r'unconnected|left|right|rear|front'
    r'))?'
    r'(_edge)?'
    r'$'
)

# 输出表格的中文列名（顺序即输出顺序）
OUTPUT_COLUMNS = [
    '类型', 'ID', '名称', '形似',
    '当前贴图', '完成状态', '提交', '贡献者', '备注',
]

# 当前贴图 / 完成状态 取值
SPRITE_HAVE = '已有'
SPRITE_LOOKS_LIKE = '形似回退'
SPRITE_MISSING = '缺失'

STATUS_MERGED = '已合并'      # 已有贴图，视为已并入贴图包
STATUS_TODO = '待领取'        # 缺失，等待认领
# 另有「进行中」「已完成」由贡献者在表中手动更新


def strip_overlay_id(overlay_id: str) -> str:
    """
    Extract game ID from an overlay ID string

    >>> strip_overlay_id('vp_wheel_wood')
    'wheel_wood'
    >>> strip_overlay_id('vp_reinforced_windshield_front_edge')
    'reinforced_windshield'
    >>> strip_overlay_id('vp_wheel_wheelchair')
    'wheel_wheelchair'
    >>> strip_overlay_id('vp_frame_wood_vertical_2_unconnected')
    'frame_wood'

    """
    stripped_id = overlay_id

    for pattern in REPLACEMENTS:
        stripped_id = re.sub(
            pattern,
            r'\g<1>',
            overlay_id,
        )

    stripped_id = re.sub(
        DELETION_RE,
        '',
        stripped_id,
    )

    return stripped_id


def get_data(
        all_game_ids_filename: str,
        overlay_ids_filename: str,
        tileset_ids_filename: str)\
        -> tuple:
    """
    Load datasets with game IDs, tileset IDs and overlay IDs
    """
    all_game_ids = pandas.read_csv(
        all_game_ids_filename,
        on_bad_lines='warn',
    )
    overlay_ids = pandas.read_csv(
        overlay_ids_filename,
        header=None,
        names=('overlay_id',),
        on_bad_lines='warn',
    )
    tileset_ids = pandas.read_csv(
        tileset_ids_filename,
        header=None,
        names=('tileset_id',),
        on_bad_lines='warn',
    )
    return all_game_ids, overlay_ids, tileset_ids


def merge_datasets(
        all_game_ids: Union[dict, pandas.DataFrame],
        overlay_ids: Union[dict, pandas.DataFrame],
        tileset_ids: Union[dict, pandas.DataFrame])\
        -> pandas.DataFrame:
    """
    Match IDs between game data, overlays and tileset

    （下例仅作示意，输出行顺序依赖 pandas 版本，故跳过严格比对）

    >>> merge_datasets({  # doctest: +SKIP
    ...     'type': ['ARMOR', 'TOOL', 'BOOK'],
    ...     'id': ['a', 'b', 'c'],
    ...     'description': ['desc a', 'desc b', 'desc c'],
    ...     'color': ['red', 'green', 'blue']
    ... }, {
    ...     'overlay_id': [
    ...         'overlay_worn_a', 'overlay_worn_b', 'overlay_worn_c',
    ...         'overlay_wielded_a', 'overlay_wielded_b', 'overlay_wielded_c',
    ...     ],
    ... }, {
    ...     'tileset_id': ['a', 'b', 'overlay_worn_a', 'overlay_wielded_b'],
    ... })
        type id description  color         overlay_id         tileset_id
    0  ARMOR  a      desc a    red                NaN                  a
    1  ARMOR  a      desc a    red     overlay_worn_a     overlay_worn_a
    7    NaN  a         NaN    NaN  overlay_wielded_a                NaN
    2   TOOL  b      desc b  green                NaN                  b
    3   TOOL  b      desc b  green  overlay_wielded_b  overlay_wielded_b
    5    NaN  b         NaN    NaN     overlay_worn_b                NaN
    4   BOOK  c      desc c   blue                NaN                NaN
    6    NaN  c         NaN    NaN     overlay_worn_c                NaN
    8    NaN  c         NaN    NaN  overlay_wielded_c                NaN
    """
    all_game_ids = pandas.DataFrame(all_game_ids)
    overlay_ids = pandas.DataFrame(overlay_ids)
    tileset_ids = pandas.DataFrame(tileset_ids)

    tileset_ids['id'] = tileset_ids['tileset_id'].apply(strip_overlay_id)

    # TODO: output the original ID and type in the generate_overlay_ids.py
    overlay_ids['id'] = overlay_ids['overlay_id'].apply(strip_overlay_id)

    # match tileset with game data
    result = all_game_ids.merge(
        tileset_ids,
        how='outer',
        on='id',
        sort=False,
    )
    # match overlays
    result = result.merge(
        overlay_ids,
        how='outer',
        left_on=['id', 'tileset_id'],
        right_on=['id', 'overlay_id'],
        sort=False,
    )
    # rearrange columns
    overlay_id_column = result.pop('overlay_id')
    result.insert(
        result.columns.get_loc('tileset_id'),
        overlay_id_column.name,
        overlay_id_column,
    )
    return result.sort_values('id')


def build_contribution_table(merged: pandas.DataFrame) -> pandas.DataFrame:
    """
    将外连接结果聚合成每个游戏实体一行的贡献追踪表。

    - 只保留游戏真正需要贴图的实体（type 非空，来自 --tileset 的类型集合）
    - 同一 id 的多行（overlay 撑出）聚合：只要任一行匹配到 tileset_id 即视为「已有」
    - 计入 looks_like 回退：自身无贴图但 looks_like 指向的 id 有贴图 -> 形似回退
    - 追加协作空列：提交 / 贡献者 / 备注
    """
    # 仅游戏实体（type 非空）
    game = merged[merged['type'].notna()].copy()
    game['_has_direct'] = game['tileset_id'].notna()

    # 贴图包中已存在的全部 id（用于 looks_like 回退判断）
    drawn_ids = set(game.loc[game['_has_direct'], 'id'].astype(str))

    # 缺省列兜底（--tileset 若未导出某列时不报错）
    for col in ('name', 'looks_like'):
        if col not in game.columns:
            game[col] = pandas.NA

    agg = game.groupby('id', dropna=False).agg(
        type=('type', 'first'),
        name=('name', 'first'),
        looks_like=('looks_like', 'first'),
        has_direct=('_has_direct', 'max'),
    ).reset_index()

    def sprite_state(row) -> str:
        if row['has_direct']:
            return SPRITE_HAVE
        ll = row['looks_like']
        if pandas.notna(ll) and str(ll) in drawn_ids:
            return SPRITE_LOOKS_LIKE
        return SPRITE_MISSING

    def status_state(sprite: str) -> str:
        # 已有(含形似回退)默认视为已合并；真缺失为待领取
        return STATUS_TODO if sprite == SPRITE_MISSING else STATUS_MERGED

    agg['当前贴图'] = agg.apply(sprite_state, axis=1)
    agg['完成状态'] = agg['当前贴图'].apply(status_state)
    agg['提交'] = ''
    agg['贡献者'] = ''
    agg['备注'] = ''

    agg = agg.rename(columns={
        'type': '类型',
        'id': 'ID',
        'name': '名称',
        'looks_like': '形似',
    })

    # 排序：缺失优先（待领取的排前面方便认领），再按类型、ID
    sprite_order = {SPRITE_MISSING: 0, SPRITE_LOOKS_LIKE: 1, SPRITE_HAVE: 2}
    agg['_order'] = agg['当前贴图'].map(sprite_order).fillna(9)
    agg = agg.sort_values(['_order', '类型', 'ID']).drop(columns='_order')

    return agg[OUTPUT_COLUMNS]


def write_output(data: pandas.DataFrame, output_filename: str) -> int:
    """
    Write the resulting DataFrame to a file (UTF-8 with BOM so Excel 正确识别中文)
    """
    data.to_csv(output_filename, index=False, encoding='utf-8-sig')
    return 0


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    arg_parser.add_argument('all_game_ids.csv')
    arg_parser.add_argument('all_overlay_ids.csv')
    arg_parser.add_argument('tileset_ids.csv')
    arg_parser.add_argument('tileset_coverage_output.csv')
    arg_parser.add_argument(
        '--raw', action='store_true',
        help='输出未聚合的原始外连接结果（英文列），而非中文贡献追踪表',
    )
    args_dict = vars(arg_parser.parse_args())

    merged = merge_datasets(
        *get_data(
            args_dict.get('all_game_ids.csv'),
            args_dict.get('all_overlay_ids.csv'),
            args_dict.get('tileset_ids.csv'),
        )
    )

    if args_dict.get('raw'):
        output = merged
    else:
        output = build_contribution_table(merged)

    sys.exit(write_output(
        output,
        args_dict.get('tileset_coverage_output.csv'),
    ))
