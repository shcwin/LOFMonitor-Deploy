LOF基金溢价监控程序提示词：

通过akshare的fund_etf_category_sina(symbol="LOF基金")接口获取所有的LOF基金代码。将返回值的代码和名称保存再本地文件中。如果本地有LOF基金信息则直接读取本地文件，否则调用接口获取。这个接口获取的代码前面带有sz或者sh，保存的时候把这个前缀剥离，记录为market、code、name三个字段。

通过akshare的fund_lof_hist_em(symbol="160723", period="daily", start_date="20260130", end_date="20260131", adjust="") 这个接口获取LOF基金的最近的场内价格。 

通过akshare的fund_open_fund_info_em(symbol="160723")接口获取LOF基金的最新的场外价格。

让指定LOF基金的场内价格为X，场外价格为Y，溢价率Z1 = (X-Y)/ Y * 100%, 折价率Z2 = (Y - X) / X * 100%
如果一个LOF基金Z1大于一个设定的阈值比如30%，Z2大于一个设定的阈值比如40%，则通过钉钉接口发送一条消息。另外本地log文件记录该监控告警。

写一个美观且简约的UI界面，支持配置阈值，展示LOF溢价和折价的信息，并且支持筛选。





