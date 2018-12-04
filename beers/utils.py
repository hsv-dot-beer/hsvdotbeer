"""Utility functions for beers"""


def render_srm(color_srm):
    """Convert the SRM to a valid HTML string (if known)"""
    if not color_srm:
        return '#ffffff'
    # round the color to an int and put it in the inclusive range [1, 30]
    int_color = min([int(color_srm), 30])
    if int_color < 1:
        return '#ffffff'
    # source:
    # https://www.homebrewtalk.com/forum/threads/ebc-or-srm-to-color-rgb.78018/#post-820969
    color_map = {
        1: '#F3F993',
        2: '#F5F75C',
        3: '#F6F513',
        4: '#EAE615',
        5: '#E0D01B',
        6: '#D5BC26',
        7: '#CDAA37',
        8: '#C1963C',
        9: '#BE8C3A',
        10: '#BE823A',
        11: '#C17A37',
        12: '#BF7138',
        13: '#BC6733',
        14: '#B26033',
        15: '#A85839',
        16: '#985336',
        17: '#8D4C32',
        18: '#7C452D',
        19: '#6B3A1E',
        20: '#5D341A',
        21: '#4E2A0C',
        22: '#4A2727',
        23: '#361F1B',
        24: '#261716',
        25: '#231716',
        26: '#19100F',
        27: '#16100F',
        28: '#120D0C',
        29: '#100B0A',
        30: '#050B0A',
    }
    return color_map[int_color]
