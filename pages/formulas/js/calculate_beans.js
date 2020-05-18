var vm = new Vue({
	el: "#app",
	data: {
		//大豆现货压榨利润
		spotBeansProfit: "",
		mealSpotPrice: "", // 豆粕现货价格
		beanOilSpotPrice: "", // 豆油现货价格
		primeBeansCostPrice:"", //大豆成本
		processCostPrice:"",  //加工费
		
		// 大豆盘面压榨利润
		diskBeansProfit: "",
		beanOilFuturePrice: "" , // 豆油期价
		mealFuturePrice: "", // 豆粕期价
		CBOTPointPrice: "", // CBOT点价
		pointCount: "", // 点价数量
		beanPrimiun: "", // 升贴水
		beanLossWare: "", // 损耗
		spotRate: "", // 即期汇率
		NDForwards: "", // 无本金交割远期外汇交易
		domestocLockRate: "", // 国内锁定汇率
		insurancePrice: "", // 保险
		middleCost: "", // 中转费用	
		
		// 大豆进口成本
		beansImportCost: "", // 进口成本
		CBOTFuturesPrice: "", // CBOT期价
		FOBPrimiun: "", // FOB升贴水
		unitReverseRatio: "", // 单位转换系数
		seaTrafficCost: "", // 海运费
		addedTax: "", //增值税
		tariff: "", // 关税
		RMBRate: "", // 人民币汇率
		seaMixedCost: "", // 港杂费
		
		// 出粕量
		generateMealAmount: "", // 出粕量
		mealPressAmount: "", // 压榨量 
		
		// 出油量
		genarateOilAmount: "", // 出油量
		oilPressAmount: "", // 压榨量
	},
	watch:{
		//大豆现货压榨利润
		mealSpotPrice(val, oldVal){
			this.spotBeansProfit = this.calculateSpotBeansProfit();
		},
		beanOilSpotPrice(val, oldVal){
			this.spotBeansProfit = this.calculateSpotBeansProfit();
		},
		primeBeansCostPrice(val, oldVal){
			this.spotBeansProfit = this.calculateSpotBeansProfit();
		},
		processCostPrice(val, oldVal){
			this.spotBeansProfit = this.calculateSpotBeansProfit();
		},
		// 大豆盘面压榨利润
		beanOilFuturePrice(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		mealFuturePrice(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		CBOTPointPrice(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		pointCount(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		beanPrimiun(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		beanLossWare(val, oldVal){
			console.log(11);
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		spotRate(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		NDForwards(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		domestocLockRate(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		insurancePrice(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		middleCost(val, oldVal){
			this.diskBeansProfit = this.calculateDiskBeansProfit();
		},
		// 大豆进口成本
		CBOTFuturesPrice(val, oldVal){
			this.beansImportCost = this.calculateImportCost();
		},
		FOBPrimiun(val, oldVal){
			this.beansImportCost = this.calculateImportCost();
		},
		unitReverseRatio(val, oldVal){
			this.beansImportCost = this.calculateImportCost();
		},
		seaTrafficCost(val, oldVal){
			this.beansImportCost = this.calculateImportCost();
		},
		addedTax(val, oldVal){
			this.beansImportCost = this.calculateImportCost();
		},
		tariff(val, oldVal){
			this.beansImportCost = this.calculateImportCost();
		},
		RMBRate(val, oldVal){
			this.beansImportCost = this.calculateImportCost();
		},
		seaMixedCost(val, oldVal){
			this.beansImportCost = this.calculateImportCost();
		},
		// 出粕量
		
		mealPressAmount(){
			this.generateMealAmount = this.caculateGenerateMeal();
		},
		// 出油量
		oilPressAmount(){
			this.genarateOilAmount = this.caculateGenerateOil();
		}
		
	},
	methods:{
		//大豆现货压榨利润
		calculateSpotBeansProfit(){
			var profitResult;
			profitResult = parseFloat(this.mealSpotPrice) * 0.19 - parseFloat(this.primeBeansCostPrice) - parseFloat(this.processCostPrice);
			return Math.round(profitResult);
		},
		// 大豆盘面压榨利润
		calculateDiskBeansProfit(){
			var futuresPrice;
			futuresPrice = parseFloat(this.beanOilFuturePrice) * 0.19 + parseFloat(this.mealFuturePrice )* 0.785;
			var rateResult;
			rateResult = (parseFloat(this.CBOTPointPrice) / parseFloat(this.pointCount) + parseFloat(this.beanPrimiun)) * 0.367433 * (parseFloat(this.spotRate) + parseFloat(this.NDForwards) + parseFloat(this.domestocLockRate)) * 1.11 * 1.03 + parseFloat(this.insurancePrice) + parseFloat(this.middleCost) + parseFloat(this.beanLossWare);
			console.log(rateResult);
			return Math.round(futuresPrice - rateResult);
		},
		// 大豆进口成本计算
		calculateImportCost(){
			var resultValue;
			resultValue = ((parseFloat(this.CBOTFuturesPrice) + parseFloat(this.FOBPrimiun)) * parseFloat(this.unitReverseRatio) + parseFloat(this.seaTrafficCost)) * (1 + parseFloat(this.addedTax)) * (1 + parseFloat(this.tariff)) * parseFloat(this.RMBRate) + parseFloat(this.seaMixedCost);
			return Math.round(resultValue);
		},
		// 出粕量计算
		caculateGenerateMeal(){
			return Math.round(parseFloat(this.mealPressAmount) * 0.785);
		},
		// 出油量计算
		caculateGenerateOil(){
			return Math.round(parseFloat(this.oilPressAmount) * 0.195);
		}
	}
});