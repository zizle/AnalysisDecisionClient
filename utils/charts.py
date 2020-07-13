# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-07-13
# ------------------------
import math
import datetime


def chart_options_handler(source_df, legend_sources, pretreatment_options):
    """
    生成echarts配置项
    :param source_df: 用于画图的源数据DataFrame
    :param legend_sources: 图例的名称源
    :param pretreatment_options: 预处理后的json配置
    :return: options
    """
    x_axis = pretreatment_options['x_axis'][0]
    # 根据x轴转数据格式
    # chart_src_data = self.get_splice_df(x_axis['col_index'])
    if x_axis['col_index'] == "column_0":
        source_df['column_0'] = source_df['column_0'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime(x_axis['date_format']))  # 转为要求的格式
    # 1 x轴数据
    option_of_xaxis = {
        "type": "category",
        "data": source_df[x_axis["col_index"]].values.tolist(),
        'axisLabel': {
            'rotate': -26,
            'fontSize': 11
        },
    }
    # 2 Y轴数据
    y_axis = [{'type': 'value',"name": pretreatment_options['axis_tags']['left']},{'type': 'value',"name": pretreatment_options['axis_tags']['right']}]
    if pretreatment_options['y_left_min']:
        y_axis[0]['min'] = pretreatment_options['y_left_min']
    if pretreatment_options['y_left_max']:
        y_axis[0]['max'] = pretreatment_options['y_left_max']
    if pretreatment_options['y_right_min']:
        y_axis[1]['min'] = pretreatment_options['y_right_min']
    if pretreatment_options['y_right_max']:
        y_axis[1]['max'] = pretreatment_options['y_right_max']
    series = list()
    legend_data = list()
    for y_left_opts_item in pretreatment_options['y_left']:  # 左轴数据
        left_series = dict()  # 左轴系列
        if y_left_opts_item['no_zero']:  # 本数据去0
            cache_df = source_df[source_df[y_left_opts_item['col_index']] != '0'].copy()
        else:
            cache_df = source_df
        left_series['type'] = y_left_opts_item['chart_type']
        left_series['name'] = legend_sources[y_left_opts_item['col_index']]
        left_series['yAxisIndex'] = 0
        a = cache_df[x_axis['col_index']].values.tolist()  # 横轴数据
        b = cache_df[y_left_opts_item['col_index']].values.tolist()  # 数值
        left_series['data'] = [*zip(a, b)]
        series.append(left_series)
        legend_data.append(legend_sources[y_left_opts_item['col_index']])

    for y_right_opts_item in pretreatment_options['y_right']:  # 右轴数据
        right_series = dict()  # 右轴系列
        if y_right_opts_item['no_zero']:  # 本数据去0
            cache_df = source_df[source_df[y_right_opts_item['col_index']] != '0'].copy()
        else:
            cache_df = source_df
        right_series['type'] = y_right_opts_item['chart_type']
        right_series['name'] = legend_sources[y_right_opts_item['col_index']]
        right_series['yAxisIndex'] = 1
        a = cache_df[x_axis['col_index']].values.tolist()  # 横轴数据
        b = cache_df[y_right_opts_item['col_index']].values.tolist()  # 数值
        right_series['data'] = [*zip(a, b)]
        series.append(right_series)
        legend_data.append(legend_sources[y_right_opts_item['col_index']])
    # 标题大小
    title_size = pretreatment_options['title']['textStyle']['fontSize']
    # 根据预处理信息绘制图形
    options = {
        "title": pretreatment_options["title"],
        'legend': {'data': legend_data, 'bottom': 13},
        'tooltip': {'axisPointer': {'type': 'cross'}},
        'grid': {
            'top': title_size + 15,
            'left': 5,
            'right': 5,
            'bottom': 20 * (len(legend_data) / 3 + 1) + 22,
            'show': False,
            'containLabel': True,
        },
        'xAxis': option_of_xaxis,
        'yAxis': y_axis,
        'series': series,
        'dataZoom': [{
            'type': 'slider',
            'start': 0,
            'end': 100,
            'bottom': 0,
            'height': 16
        }]
    }
    if pretreatment_options['watermark']:
        options['graphic'] = {
            'type': 'group',
            'rotation': math.pi / 4,
            'bounding': 'raw',
            'right': 110,
            'bottom': 110,
            'z': 100,
            'children': [
                {
                    'type': 'rect',
                    'left': 'center',
                    'top': 'center',
                    'z': 100,
                    'shape': {
                        'width': 400,
                        'height': 50
                    },
                    'style': {
                        'fill': 'rgba(0,0,0,0.3)'
                    }
                },
                {
                    'type': 'text',
                    'left': 'center',
                    'top': 'center',
                    'z': 100,
                    'style': {
                        'fill': '#fff',
                        'text': pretreatment_options["watermark_text"],
                        'font': 'bold 26px Microsoft YaHei'
                    }
                }
            ]
        }
    return options

