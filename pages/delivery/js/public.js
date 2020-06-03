//var host = "http://192.168.0.103:8000/";
var host = "http://127.0.0.1:5000/";
// 保存token
var token = localStorage.token;
// 保存地区信息让地图页面用
// var areaJson = JSON.parse(localStorage.areaJson);

var areaJson = [
    {name:"北京市",s_name:"北京"},
    {name:"天津市",s_name:"天津"},
    {name:"上海市",s_name:"上海"},
    {name:"重庆市",s_name:"重庆"},
    {name:"河北省",s_name:"河北"},
    {name:"山西省",s_name:"山西"},
    {name:"辽宁省",s_name:"辽宁"},
    {name:"吉林省",s_name:"吉林"},
    {name:"黑龙江省",s_name:"黑龙江"},
    {name:"江苏省",s_name:"江苏"},
    {name:"浙江省",s_name:"浙江"},
    {name:"安徽省",s_name:"安徽"},
    {name:"福建省",s_name:"福建"},
    {name:"江西省",s_name:"江西"},
    {name:"山东省",s_name:"山东"},
    {name:"河南省",s_name:"河南"},
    {name:"湖北省",s_name:"湖北"},
    {name:"湖南省",s_name:"湖南"},
    {name:"广东省",s_name:"广东"},
    {name:"海南省",s_name:"海南"},
    {name:"四川省",s_name:"四川"},
    {name:"贵州省",s_name:"贵州"},
    {name:"云南省",s_name:"云南"},
    {name:"陕西省",s_name:"陕西"},
    {name:"甘肃省",s_name:"甘肃"},
    {name:"青海省",s_name:"青海"},
    {name:"台湾省",s_name:"台湾"},
    {name:"内蒙古自治区",s_name:"内蒙古"},
    {name:"广西壮族自治区",s_name:"广西"},
    {name:"西藏自治区", s_name:"西藏"},
    {name:"宁夏回族自治区",s_name:"宁夏"},
    {name:"新疆维吾尔自治区", s_name:"新疆"},
    {name:"香港特别行政区",s_name:"香港"},
    {name:"澳门特别行政区",s_name:"澳门"}
];

