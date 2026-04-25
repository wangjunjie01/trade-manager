# 贸易公司内部管理系统

## 📋 功能

- **📋 送货单管理**：创建、查看送货单，记录产品明细
- **💰 打款记录**：记录客户付款，支持关联送货单
- **📊 对账汇总**：一键查看各客户应收/已收/欠款情况
- **🏢 客户管理**：管理客户信息
- **📦 产品管理**：管理产品目录和价格

## 🚀 快速部署

### 方法一：Streamlit Cloud（推荐，免费）

1. 将此仓库 Fork 到你的 GitHub
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 用 GitHub 登录，授权 Streamlit Cloud
4. 点击 "Deploy an app"
5. 选择仓库 `your-username/trade-manager`
6. Branch 选择 `main`，Main file path 填写 `app.py`
7. 点击 Deploy！

### 方法二：本地运行

```bash
# 克隆仓库
git clone https://github.com/wangjunjie01/trade-manager.git
cd trade-manager

# 安装依赖
pip install -r requirements.txt

# 运行
streamlit run app.py
```

## 📌 注意事项

- 数据存储在本地 `data.json` 文件中
- 部署到云端时，数据不会持久保存（重启后会重置）
- 如需持久化，请连接数据库

## 🔧 后续可扩展功能

- [ ] PDF 导出功能
- [ ] 用户权限管理
- [ ] 数据库连接（PostgreSQL/MySQL）
- [ ] 报价单生成
- [ ] 库存预警
- [ ] 报表导出 Excel
