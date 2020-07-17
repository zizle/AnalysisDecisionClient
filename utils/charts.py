# _*_ coding:utf-8 _*_
# Author： zizle
# Created:2020-07-13
# ------------------------
import math
import datetime


def datazoom_option():
    return [{
        'type': 'slider',
        'start': 0,
        'end': 100,
        'bottom': 0,
        'height': 16
    }]


def graphic_option(text):
    return {
        'type': 'group',
        'rotation': math.pi / 4,
        'bounding': 'raw',
        'right': 80,
        'bottom': 80,
        'z': 100,
        'children': [
            {
                'type': 'rect',
                'left': 'center',
                'top': 'center',
                'z': 100,
                'shape': {
                    'width': 400,
                    'height': 35
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
                    'text': text,
                    'font': 'bold 22px Microsoft YaHei'
                }
            }
        ]
    }


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
            'rotate': 90,
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
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'line'
            },
            'backgroundColor': 'rgba(245, 245, 245, 0.8)',
            'borderWidth': 1,
            'borderColor': '#ccc',
            'padding': 10,
            'textStyle': {
                'color': '#000'
            },
        },
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


# 季节图形的配置
def season_chart_options_handler(source_df, pretreatment_options, has_datazoom=False):
    # 去0的设置
    y_left = pretreatment_options['y_left'][0]
    if y_left['no_zero']:
        chart_src_data = source_df[source_df[y_left['col_index']] != '0'].copy()
    else:
        chart_src_data = source_df.copy()
    # 进行数据年的处理
    x_axis = pretreatment_options['x_axis'][0]
    start_date = x_axis['start']
    if not start_date:
        start_date = chart_src_data.iloc[0]['column_0']
    end_date = x_axis['end']
    if not end_date:
        end_date = chart_src_data.iloc[chart_src_data.shape[0] - 1]['column_0']
    # 生成起始日期的年份列表
    date_list = [datetime.datetime.strptime(str(date), "%Y").strftime('%Y-%m-%d') for date in range(int(start_date[:4]), int(end_date[:4]) + 1)]
    if len(date_list) <= 0:
        return {}
    min_index, max_index = 0, len(date_list) - 1
    split_data_dict = dict()
    # if len(date_list) > 1:
    while min_index < max_index:
        year_data_frame = chart_src_data[(date_list[min_index] <= chart_src_data['column_0']) & (chart_src_data['column_0'] < date_list[min_index + 1])].copy()
        year_data_frame['column_0'] = year_data_frame['column_0'].apply(lambda x: x[5:])
        split_data_dict[date_list[min_index]] = year_data_frame
        min_index += 1
    year_data_frame = chart_src_data[date_list[max_index] <= chart_src_data['column_0']].copy()  # 条件不一致，min_index=max_index时
    year_data_frame['column_0'] = year_data_frame['column_0'].apply(lambda x: x[5:])
    split_data_dict[date_list[max_index]] = year_data_frame
    # 4 生成x横轴信息,获取y轴数据进行绘图
    x_start, x_end = datetime.datetime.strptime('20200101', '%Y%m%d'), datetime.datetime.strptime('20201231', '%Y%m%d')
    x_axis_label = list()
    while x_start <= x_end:
        x_axis_label.append(x_start.strftime('%m-%d'))
        x_start += datetime.timedelta(days=1)
    # print(x_axis)
    # 4-1 生成y轴的配置
    # print(split_data_dict)
    y_axis = [{'type': 'value', "name": pretreatment_options['axis_tags']['left']}]
    if pretreatment_options['y_left_min']:
        y_axis[0]['min'] = pretreatment_options['y_left_min']
    if pretreatment_options['y_left_max']:
        y_axis[0]['max'] = pretreatment_options['y_left_max']
    series = list()
    legend_data = list()
    for series_dict_item in pretreatment_options['y_left']:
        for date_key in date_list:
            source_df = split_data_dict[date_key]
            left_series = dict()
            left_series['type'] = series_dict_item['chart_type']
            left_series['name'] = date_key[:4]
            left_series['yAxisIndex'] = 0
            a = source_df['column_0'].values.tolist()  # 时间
            b = source_df[series_dict_item['col_index']].values.tolist()  # 数值
            left_series['data'] = [*zip(a, b)]
            series.append(left_series)
            legend_data.append(date_key[:4])
    # 5 生成配置项进行绘图
    title_size = pretreatment_options['title']['textStyle']['fontSize']
    # 设计图形距离底部的高度(为图例留出空间)
    legend_length = len(legend_data)
    if legend_length // 8 == 0:  # 小于8个
        bottom_gap = 40
    else:
        if legend_length % 8 == 0:  # 整除
            bottom_gap = 35 * legend_length // 8
        else:
            bottom_gap = 30 * (legend_length // 8 + 1)

    options = {
        'title': pretreatment_options["title"],
        'legend': {'data': legend_data, 'bottom':17,'height': 20},
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'line'
            },
            'backgroundColor': 'rgba(245, 245, 245, 0.8)',
            'borderWidth': 1,
            'borderColor': '#ccc',
            'padding': 10,
            'textStyle': {
                'color': '#000'
            },
        },
        'grid': {
            'top': title_size + 15,
            'left': 5,
            'right': 5,
            'bottom': bottom_gap + 17,
            'show': False,
            'containLabel': True,
        },
        'xAxis': {
            'type': 'category',
            'data': x_axis_label,
            'axisLabel': {
                'rotate': -26,
                'fontSize': 11
            }
        },
        'yAxis': y_axis,
        'series': series,
    }
    if has_datazoom:
        options['dataZoom'] = datazoom_option()
    if pretreatment_options['watermark']:
        options['graphic'] = graphic_option(pretreatment_options["watermark_text"])
    return options
