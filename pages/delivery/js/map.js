var mapBoxEchart = null;
var cacheData = null;
var provinceData = [
    // 华北地区
    {name: '北京', itemStyle:{areaColor: '#9AB464'}},
    {name: '天津', itemStyle:{areaColor: '#9AB464'}},
    {name: '河北', itemStyle:{areaColor: '#9AB464'}},
    {name: '山西', itemStyle:{areaColor: '#9AB464'}},
    {name: '内蒙古', itemStyle:{areaColor: '#9AB464'}},
    // 东北地区
    {name: '辽宁', itemStyle:{areaColor: '#9DC9F8'}},
    {name: '吉林', itemStyle:{areaColor: '#9DC9F8'}},
    {name: '黑龙江', itemStyle:{areaColor: '#9DC9F8'}},
    // 华东地区
    {name: '上海', itemStyle:{areaColor: '#00CCFF'}},
    {name: '江苏', itemStyle:{areaColor: '#00CCFF'}},
    {name: '浙江', itemStyle:{areaColor: '#00CCFF'}},
    {name: '安徽', itemStyle:{areaColor: '#00CCFF'}},
    {name: '福建', itemStyle:{areaColor: '#00CCFF'}},
    {name: '江西', itemStyle:{areaColor: '#00CCFF'}},
    {name: '山东', itemStyle:{areaColor: '#00CCFF'}},
    // 中南地区
    {name: '河南', itemStyle:{areaColor: '#CEFFCF'}},
    {name: '湖北', itemStyle:{areaColor: '#CEFFCF'}},
    {name: '湖南', itemStyle:{areaColor: '#CEFFCF'}},
    {name: '广东', itemStyle:{areaColor: '#CEFFCF'}},
    {name: '广西', itemStyle:{areaColor: '#CEFFCF'}},
    {name: '海南', itemStyle:{areaColor: '#CEFFCF'}},
    // 西南
    {name: '重庆', itemStyle:{areaColor: '#FFFF9A'}},
    {name: '四川', itemStyle:{areaColor: '#FFFF9A'}},
    {name: '贵州', itemStyle:{areaColor: '#FFFF9A'}},
    {name: '云南', itemStyle:{areaColor: '#FFFF9A'}},
    {name: '西藏', itemStyle:{areaColor: '#FFFF9A'}},
    // 西北地区
    {name: '陕西', itemStyle:{areaColor: '#FFCC00'}},
    {name: '甘肃', itemStyle:{areaColor: '#FFCC00'}},
    {name: '青海', itemStyle:{areaColor: '#FFCC00'}},
    {name: '宁夏', itemStyle:{areaColor: '#FFCC00'}},
    {name: '新疆', itemStyle:{areaColor: '#FFCC00'}},
    // 港澳台
    {name: '香港', itemStyle:{areaColor: '#5ac8ad'}},
    {name: '澳门', itemStyle:{areaColor: '#5ac8ad'}},
    {name: '台湾', itemStyle:{areaColor: '#5ac8ad'}},

];
var option = {
        backgroundColor: '#ABDFFF',
        title: {
            text: '全国主要仓库分布',
            // subtext: 'data from PM25.in',
            // sublink: 'http://www.pm25.in',
            x:'center',
            textStyle: {
                color: '#fff'
            }
        },
        // 鼠标悬浮提示
        tooltip: {
            trigger: 'item',
            formatter: function (params) {
                return params.name;  // 提示样式
            }
        },
        // 图例全选
        legend: {
            orient: 'vertical',
            y: 'bottom',
            x: 'left',
            data:['仓库'],
            textStyle: {
                color: '#fff'
            }
        },
        // 图例
        // visualMap: {
        //     min: 0,
        //     max: 200,
        //     calculable: true,
        //     inRange: {
        //         color: ['#50a3ba', '#eac736', '#d94e5d']
        //     },
        //     textStyle: {
        //         color: '#fff'
        //     }
        // },

        // 图表类型
        geo:{
            map:'china',
            zoom: 1.3, // 初始缩放大小
            label: {show:true},  // 显示省份名称
            regions:provinceData,
            itemStyle: {
            normal: {

            },
            emphasis: {
                areaColor: '#999999'
            }
        }
        },
        // 支持'move'平移和'scale'缩放: true
        roam: true,
        // 限制缩放的比例
        scaleLimit:{
            min:1,
            max:5
        },
        // 数据
        series: [
            {
                name: '仓库',
                type: 'scatter',  // 散点图
                coordinateSystem: 'geo',
                // data:[
                //     {name: "label", value: [经度，纬度，数值]}
                //     可以单独设置symbol:
                //     {name: '上海国储天威仓储有限公司', value: [121.242354,31.297771, 250],},
                //
                //
                // ],
                data: [],
                symbolSize: 15,
                // 可以全局设置symbol
                symbol:'image://media/markPoint1.png',
                label: {
                    normal: {
                        show: false // 显示value
                    },
                    emphasis: {
                        show: false  // 鼠标悬浮显示value
                    }
                },
                itemStyle: {
                    emphasis: {
                        borderColor: '#000',
                        borderWidth: 1
                    }
                },
            }
        ]
    };

$(function () {
    var storehouseData = [];
    // 基于准备好的dom，初始化echarts实例
    mapBoxEchart = echarts.init(document.getElementById('mapBox'));
    option.series[0].data = storehouseData;
    // 使用制定的配置项和数据显示图表
    mapBoxEchart.setOption(option, true);
    new QWebChannel(qt.webChannelTransport, function(channel){
        var pageContact = channel.objects.pageContactChannel;
        window.pageChannel = pageContact;
        pageContact.refresh_warehouses.connect(function (warehouses) {
            storehouseData.splice(0);
            $.each(warehouses, function (hindx, house) {
                storehouseData.push({
                    name: house.name,
                    value: [house.longitude, house.latitude],
                    hid:house.id,
                })
            });
            // 重新设置数据，重新加载地图
            option.series[0].data = storehouseData;  // 改变数据
            mapBoxEchart.setOption(option, true);
        });
        // 设置高度
        pageContact.resize_map.connect(function (newWidth, newHeight) {
            mapBoxEchart.resize({width: newWidth, height: newHeight});
        })

        // pageContact.senderUserToken.connect(function (userToken) {
        //     localStorage.token = userToken;  // 设置token，存入本地存储
        //     token = localStorage.token;
        //     pageContact.hasReceivedUserToken(true);  // 发消息告诉界面收到了token
        // });
    });



    // 获取所有交割库的信息
    // $.ajax({
    //     url: host + 'delivery/storehouses/',
    //     async:false,
    //     type: 'get',
    //     success: function (res) {
    //         // console.log(res);
    //         $.each(res.data, function (hindx, house) {
    //             storehouseData.push({
    //                 name: house.name,
    //                 value: [house.longitude, house.latitude],
    //                 hid:house.id,
    //             })
    //         })
    //     },
    //     error: function (res) {
    //         // console.log(res)
    //     }
    // });

    // // 基于准备好的dom，初始化echarts实例
    // mapBoxEchart = echarts.init(document.getElementById('mapBox'));
    // option.series[0].data = storehouseData;
    // var option = {
    //     backgroundColor: '#CDB',
    //     title: {
    //         text: '全国主要仓库分布',
    //         // subtext: 'data from PM25.in',
    //         // sublink: 'http://www.pm25.in',
    //         x:'center',
    //         textStyle: {
    //             color: '#fff'
    //         }
    //     },
    //     // 鼠标悬浮提示
    //     tooltip: {
    //         trigger: 'item',
    //         formatter: function (params) {
    //             return params.name;  // 提示样式
    //         }
    //     },
    //     // 全选
    //     legend: {
    //         orient: 'vertical',
    //         y: 'bottom',
    //         x: 'right',
    //         data:['仓库'],
    //         textStyle: {
    //             color: '#fff'
    //         }
    //     },
    //     // 图例
    //     // visualMap: {
    //     //     min: 0,
    //     //     max: 200,
    //     //     calculable: true,
    //     //     inRange: {
    //     //         color: ['#50a3ba', '#eac736', '#d94e5d']
    //     //     },
    //     //     textStyle: {
    //     //         color: '#fff'
    //     //     }
    //     // },
    //     // 图类型
    //     geo:{
    //         map:'china',
    //         zoom: 1.5, // 初始缩放大小
    //         label: {show:true}  // 显示省份名称
    //     },
    //     // 支持'move'平移和'scale'缩放: true
    //     roam: true,
    //     // 限制缩放的比例
    //     scaleLimit:{
    //         min:1,
    //         max:5
    //     },
    //     // 数据
    //     series: [
    //         {
    //             name: '仓库',
    //             type: 'scatter',
    //             coordinateSystem: 'geo',
    //             // data:[
    //             //     {name: "label", value: [经度，纬度，数值]}
    //             //     可以单独设置symbol:
    //             //     {name: '上海国储天威仓储有限公司', value: [121.242354,31.297771, 250],},
    //             //
    //             //
    //             // ],
    //             data: storehouseData,
    //             symbolSize: 15,
    //             // 可以全局设置symbol
    //             symbol:'image://media/markPoint.png',
    //             label: {
    //                 normal: {
    //                     show: false // 显示value
    //                 },
    //                 emphasis: {
    //                     show: false  // 鼠标悬浮显示value
    //                 }
    //             },
    //             itemStyle: {
    //                 emphasis: {
    //                     borderColor: '#fff',
    //                     borderWidth: 1
    //                 }
    //             },
    //         }
    //     ]
    // };

    // echarts 图表自适应
    // window.addEventListener("resize", function() {
    //     mapBoxEchart.resize();
    // });
    // 点击事件
    mapBoxEchart.on('click', function (event) {
        // console.log(event)
        var eventOption = event['componentType'];
        if (eventOption == 'geo') {
            // 向界面发送请求身份的仓库信号
            // alert(event.name);
            window.pageChannel.get_province_warehouses(event.name);
        }
        else if(eventOption == 'series')
        {
            // 仓库详情
            var storeId = event['data']['hid'];
            // alert(storeId);
            window.pageChannel.get_warehouse_detail(storeId);
        }
        //
        //
        //     // var cacheData = null;
        //     // 下方添加省份详情的页面
        //     // 获取省份的全名称
        //     var province = "";
        //     //
        //      $.each(areaJson, function (hindx, areaObj) {
        //         if(areaObj.s_name == event['name']){
        //             province = areaObj.name;
        //             // alert(province)
        //         }
        //     });
        //     // var provinceEN = areaJson[(event['name'])];
        //     if (!province){
        //         $('.clickDetail').html("*暂无相关数据");
        //         adjustFrameSize();  // 调整iframe的大小
        //     }else{
        //         // 请求省模式下仓库信息
        //         $.ajax({
        //             url: host + 'delivery/storehouse/' + province + '/',
        //             type: 'get',
        //             success: function (res) {
        //                 // console.log(provinceEN + "仓库信息：",res);
        //                 var res = res.data;
        //                 if (isEmpty(res)){
        //                     res['province']=event['name'];
        //                     res['count'] = 0;
        //                 }
        //                 // 渲染数据
        //                 var provinceDetail = "<span>【" + res['province'] + "交割库】(" + res['count'] +"家)</span>";
        //                 delete res['province'];
        //                 delete res['count'];
        //                 $.each(res, function (variety, varietyHouses) {
        //                     provinceDetail += "<div class='house-leader'>" + variety + "</div>";
        //                     provinceDetail += "<div class='house-list'>";
        //                     provinceDetail += "<ul>";
        //                     $.each(varietyHouses, function (idx, house) {
        //                         provinceDetail += "<li data-value="+ house['id']+">" + house['name'] + "</li>";
        //                     });
        //                     provinceDetail += "</ul>";
        //                 });
        //                 $('.clickDetail').html(provinceDetail);
        //                 cacheData = provinceDetail;  // 缓存内容用于返回显示
        //                 adjustFrameSize();  // 调整iframe的大小
        //
        //             },
        //             error: function (res) {
        //                 console.log(res)
        //             }
        //         });
        //     }
        // }else if(eventOption == 'series'){
        //     // 下方添加仓库详情的页面
        //     var storeId = event['data']['hid'];
        //     // console.log(storeId);
        //     // 仓库详情数据
        //     $.ajax({
        //         url: host + 'delivery/storehouse/' + storeId + '/',
        //         type: 'get',
        //         success: function (res) {
        //             // console.log(res)
        //             var res = res.data;
        //             var detailHouseData = {
        //                 name: res.name,
        //                 arrived:res.arrived,
        //                 pad:res.premium,
        //                 address:res.address,
        //                 contacts: res.link,
        //                 tel:res.tel_phone,
        //                 fax:res.fax,
        //                 reports: res.reports,
        //             };
        //             var houseDetail = getHouseDetailHtml(detailHouseData);
        //             $(".clickDetail").html(houseDetail);
        //             adjustFrameSize();  // 调整iframe的大小
        //         },
        //         error: function (res) {
        //             console.log(res)
        //         }
        //     });
        // }else{}
        // parent.$('html,body').animate({scrollTop:'240px'},400);
    });
     // 仓库点击显示详情
    $('.clickDetail').on('click', 'li', function () {
            // 显示详情
            var houseId = $(this).data('value');
            if (typeof (houseId) == "undefined"){
                return false; // 防止仓库详情里的li被点击发送请求
            }
            // ajax获取仓库详情
            $.ajax({
                url: host + 'delivery/storehouse/' + houseId + '/',
                type: 'get',
                success: function (res) {
                    // console.log(res);
                    var res=res.data;
                    var detailHouseData = {
                        name: res.name,
                        arrived:res.arrived,
                        pad:res.premium,
                        address:res.address,
                        contacts: res.link,
                        tel:res.tel_phone,
                        fax:res.fax,
                        reports: res.reports,
                    };
                    var houseDetail = getHouseDetailHtml(detailHouseData);
                    $(".clickDetail").html(houseDetail)
                    $(".clickDetail").append("<div><button class='backward'>返回</button></div>");
                    // 返回的点击事件
                    $('.backward').on('click', function () {
                        $('.clickDetail').html(cacheData)
                    });
                    adjustFrameSize();  // 调整iframe的大小

                },
                error: function (res) {
                    console.log(res)
                }
            });
        });
});

// 显示仓库详情信息
function getHouseDetailHtml(detailHouseData) {
    var houseDetail = "<div class='shDetail'><span>【" + detailHouseData['name'] + "】</span>";
    houseDetail += "<ul>";
    houseDetail += "<li>到达站、港：" + detailHouseData["arrived"] + "</li>";
    houseDetail += "<li>升贴水：" + detailHouseData["pad"] + "</li>";
    houseDetail += "<li>存放地址：" + detailHouseData["address"] + "</li>";
    houseDetail += "<li>联系人：" + detailHouseData["contacts"] + "</li>";
    houseDetail += "<li>电话：" + detailHouseData["tel"] + "</li>";
    houseDetail += "<li>传真：" + detailHouseData["fax"] + "</li>";
    houseDetail += "</div>";
    // 仓单日报
    var reportTitle = ['日期','仓库', '昨日仓单','今日仓单', '增减'];
    var tablesName = "<div class='tablesName'>「仓单信息」</div>";
    var tableContent = '';
    $.each(detailHouseData.reports, function (variety, vreport) {
        tableContent += "<table cellspacing='1' >";
        tableContent += '<span>品种：'+variety+'</span><tr>';
        $.each(reportTitle, function (index, value) {
            tableContent += '<th>' + value + '</th>';
        });
        $.each(vreport, function (rindx, report) {
            tableContent += '</tr><tr>';
            tableContent += "<td>" +report.date + "</td>";
            tableContent += "<td>" +report.house_name + "</td>";
            tableContent += "<td>" +report.yesterday_report + "</td>";
            tableContent += "<td>" +report.today_report + "</td>";
            tableContent += "<td>" +report.regulation + "</td>";
            tableContent += '</tr>';
        });

    });
    houseDetail += "<div class='daily-report'>";
    houseDetail += tablesName;
    houseDetail += tableContent;
    houseDetail += "</div>";
    return houseDetail
}

// 判空
function isEmpty(obj) {
	for (var o in obj){
		return false
	}
	return true
}
