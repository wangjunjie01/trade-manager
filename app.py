"""
贸易公司内部管理系统 - MVP (Supabase版 + 用户登录)
送货单管理 & 对账系统
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
import hashlib
import requests

# ============ Supabase 配置 ============
SUPABASE_URL = "https://tuzfagnvwmnsojxvdyvd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR1emZhZ252d21uc29qeHZkeXZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcwOTY0NDQsImV4cCI6MjA5MjY3MjQ0NH0.Fdxv-Xg1fW1oVKswXo5qqlMxGThUra3nAm33VtFsF2Q"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR1emZhZ252d21uc29qeHZkeXZkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzA5NjQ0NCwiZXhwIjoyMDkyNjcyNDQ0fQ.X3QhKJ7V9YHN8b9VJG7pJGpJGpJGpJGpJGpJGpJGpJGp"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

SERVICE_HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# ============ 认证相关函数 ============
def init_auth_state():
    """初始化认证状态"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "送货单"

def check_user_exists(username):
    """检查用户是否存在"""
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None

def get_all_users():
    """获取所有用户"""
    url = f"{SUPABASE_URL}/rest/v1/users?order=created_at.desc"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json()
    return []

def verify_user(username, password):
    """验证用户登录"""
    user = check_user_exists(username)
    if user:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.get("password_hash") == password_hash:
            return user
    return None

def login_user(username, name):
    """登录用户"""
    st.session_state.authenticated = True
    st.session_state.user = {"username": username, "name": name}

def logout_user():
    """登出用户"""
    st.session_state.authenticated = False
    st.session_state.user = None

def update_password(username, new_password):
    """更新密码"""
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    data = {"password_hash": password_hash}
    try:
        resp = requests.patch(url, headers=HEADERS, json=data)
        return resp.status_code in [200, 201, 204]
    except:
        return False

def create_user_in_db(username, password, name, role="user"):
    """在数据库中创建用户"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user_id = hashlib.md5(username.encode()).hexdigest()[:12]
    
    user_data = {
        "id": user_id,
        "username": username,
        "password_hash": password_hash,
        "name": name,
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    
    url = f"{SUPABASE_URL}/rest/v1/users"
    try:
        resp = requests.post(url, headers=HEADERS, json=user_data)
        return resp.status in [200, 201, 204]
    except:
        return False

# ============ 登录页面 ============
def render_login_page():
    """渲染登录页面"""
    st.markdown("""
    <style>
    .login-title {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 40px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="login-title">📦 贸易管理系统</h1>', unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("👤 账号", placeholder="输入账号")
        password = st.text_input("🔒 密码", type="password", placeholder="输入密码")
        
        st.form_submit_button("登录", use_container_width=True)
        
        if username and password:
            user = verify_user(username, password)
            if user:
                login_user(username, user.get("name", username))
                st.success("✅ 登录成功！")
                st.rerun()
            elif check_user_exists(username):
                st.error("❌ 密码错误")
            else:
                st.error("❌ 账号不存在，请联系管理员创建")
    
    st.info("💡 没有账号？请联系管理员创建")

# ============ Supabase API 操作 ============
def supabase_select(table, params=""):
    """查询数据"""
    url = f"{SUPABASE_URL}/rest/v1/{table}{params}"
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            return resp.json()
        return []
    except:
        return []

def supabase_insert(table, data):
    """插入数据"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        resp = requests.post(url, headers=HEADERS, json=data)
        return resp.status_code in [200, 201, 204]
    except:
        return False

def supabase_delete(table, filters):
    """删除数据"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        resp = requests.delete(url, headers=HEADERS, params=filters)
        return resp.status_code in [200, 201, 204]
    except:
        return False

# ============ 数据加载（带缓存） ============
@st.cache_data(ttl=60)
def load_clients():
    return supabase_select("clients", "?order=created_at.desc")

@st.cache_data(ttl=60)
def load_products():
    return supabase_select("products", "?order=created_at.desc")

@st.cache_data(ttl=60)
def load_deliveries():
    return supabase_select("deliveries", "?order=delivery_date.desc")

@st.cache_data(ttl=60)
def load_payments():
    return supabase_select("payments", "?order=payment_date.desc")

@st.cache_data(ttl=60)
def load_delivery_items(delivery_id):
    return supabase_select("delivery_items", f"?delivery_id=eq.{delivery_id}")

# ============ 供应链数据加载 ============
@st.cache_data(ttl=60)
def load_suppliers():
    return supabase_select("suppliers", "?order=created_at.desc")

@st.cache_data(ttl=60)
def load_supplier_contacts(supplier_id=None):
    if supplier_id:
        return supabase_select("supplier_contacts", f"?supplier_id=eq.{supplier_id}&order=created_at.desc")
    return supabase_select("supplier_contacts", "?order=created_at.desc")

@st.cache_data(ttl=60)
def load_supplier_materials(supplier_id=None):
    if supplier_id:
        return supabase_select("supplier_materials", f"?supplier_id=eq.{supplier_id}&order=created_at.desc")
    return supabase_select("supplier_materials", "?order=created_at.desc")

# ============ 页面配置 ============
st.set_page_config(
    page_title="贸易管理系统",
    page_icon="📦",
    layout="wide"
)

# 自定义样式
st.markdown("""
<style>
.stButton > button { width: 100%; }
.main-header { font-size: 2rem; font-weight: bold; color: #1f77b4; text-align: center; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

# ============ 侧边栏 ============
def render_sidebar():
    with st.sidebar:
        user_name = st.session_state.user.get("name", "用户") if st.session_state.user else "用户"
        st.markdown(f"### 👤 {user_name}")
        st.divider()
        
        pages = {
            "📋 送货单管理": "送货单",
            "💰 打款记录": "打款",
            "📊 对账汇总": "对账",
            "🏢 客户管理": "客户",
            "📦 产品管理": "产品",
            "🏭 上游供应链": "供应链"
        }
        
        for label, page in pages.items():
            if st.button(label, use_container_width=True):
                st.session_state.page = page
                st.rerun()
        
        st.divider()
        
        # 用户管理入口（仅管理员可见）
        if st.button("⚙️ 用户管理", use_container_width=True):
            st.session_state.page = "用户管理"
            st.rerun()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄", help="刷新数据"):
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("🚪 退出"):
                logout_user()
                st.rerun()
        
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    return st.session_state.get("page", "送货单")

# ============ 用户管理页面 ============
def render_user_management_page():
    st.markdown("## ⚙️ 用户管理")
    
    # 修改密码
    with st.expander("🔑 修改密码", expanded=True):
        with st.form("change_password"):
            current_user = st.session_state.user.get("username", "")
            st.text_input("账号", value=current_user, disabled=True)
            new_password = st.text_input("新密码", type="password", placeholder="输入新密码（至少6位）")
            confirm_password = st.text_input("确认新密码", type="password", placeholder="再次输入新密码")
            
            if st.form_submit_button("修改密码"):
                if len(new_password) < 6:
                    st.error("❌ 密码至少需要6位")
                elif new_password != confirm_password:
                    st.error("❌ 两次密码不一致")
                else:
                    if update_password(current_user, new_password):
                        st.success("✅ 密码修改成功！")
                    else:
                        st.error("❌ 修改失败，请重试")
    
    # 创建新用户（仅管理员）
    with st.expander("➕ 创建新用户", expanded=False):
        with st.form("create_user"):
            new_username = st.text_input("账号", placeholder="输入新账号")
            new_name = st.text_input("姓名", placeholder="输入用户姓名")
            new_password = st.text_input("密码", type="password", placeholder="设置密码（至少6位）")
            confirm_password = st.text_input("确认密码", type="password", placeholder="再次输入密码")
            
            if st.form_submit_button("创建用户"):
                if not new_username or not new_name:
                    st.error("❌ 请填写完整信息")
                elif len(new_password) < 6:
                    st.error("❌ 密码至少需要6位")
                elif new_password != confirm_password:
                    st.error("❌ 两次密码不一致")
                elif check_user_exists(new_username):
                    st.error("❌ 该账号已存在")
                else:
                    if create_user_in_db(new_username, new_password, new_name):
                        st.success("✅ 用户创建成功！")
                    else:
                        st.error("❌ 创建失败，请重试")
    
    # 用户列表
    st.markdown("### 用户列表")
    users = get_all_users()
    if users:
        df = pd.DataFrame(users)
        display_cols = ["username", "name", "role", "created_at"]
        cols = [c for c in display_cols if c in df.columns]
        df_display = df[cols].copy()
        df_display.columns = ["账号", "姓名", "角色", "创建时间"]
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("暂无用户")

# ============ 客户管理 ============
def render_client_page():
    st.markdown("## 🏢 客户管理")
    
    with st.expander("➕ 添加新客户", expanded=False):
        with st.form("add_client"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("客户名称 *", placeholder="输入客户名称")
                contact = st.text_input("联系人", placeholder="输入联系人姓名")
            with col2:
                phone = st.text_input("电话", placeholder="输入联系电话")
                address = st.text_input("地址", placeholder="输入客户地址")
            
            if st.form_submit_button("保存客户"):
                if name:
                    new_client = {
                        "id": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
                        "name": name,
                        "contact": contact,
                        "phone": phone,
                        "address": address
                    }
                    if supabase_insert("clients", new_client):
                        st.success("✅ 客户添加成功！")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("请输入客户名称")
    
    st.markdown("### 客户列表")
    clients = load_clients()
    if clients:
        df = pd.DataFrame(clients)
        cols = [c for c in ["name", "contact", "phone", "address"] if c in df.columns]
        df_display = df[cols].copy()
        df_display.columns = ["客户名称", "联系人", "电话", "地址"]
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("暂无客户，请添加第一个客户")

# ============ 产品管理 ============
def render_product_page():
    st.markdown("## 📦 产品管理")
    
    with st.expander("➕ 添加新产品", expanded=False):
        with st.form("add_product"):
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("产品名称 *", placeholder="输入产品名称")
            with col2:
                spec = st.text_input("规格型号", placeholder="输入规格")
            with col3:
                price = st.number_input("单价 (元)", min_value=0.0, step=0.01, format="%.2f")
            
            if st.form_submit_button("保存产品"):
                if name:
                    new_product = {
                        "id": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
                        "name": name,
                        "spec": spec,
                        "price": float(price),
                        "stock": 0
                    }
                    if supabase_insert("products", new_product):
                        st.success("✅ 产品添加成功！")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("请输入产品名称")
    
    st.markdown("### 产品列表")
    products = load_products()
    if products:
        df = pd.DataFrame(products)
        cols = [c for c in ["name", "spec", "price", "stock"] if c in df.columns]
        df_display = df[cols].copy()
        df_display.columns = ["产品名称", "规格", "单价(元)", "库存"]
        df_display["单价(元)"] = df_display["单价(元)"].apply(lambda x: f"¥{float(x):.2f}")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("暂无产品，请添加第一个产品")

# ============ 送货单管理 ============
def render_delivery_page():
    st.markdown("## 📋 送货单管理")
    clients = load_clients()
    products = load_products()
    
    with st.expander("➕ 创建新送货单", expanded=False):
        with st.form("add_delivery"):
            col1, col2 = st.columns(2)
            with col1:
                client_name = st.selectbox("选择客户 *", 
                    options=[""] + [c["name"] for c in clients], index=0)
                delivery_date = st.date_input("送货日期", value=date.today())
            with col2:
                remark = st.text_input("备注", placeholder="可选备注信息")
            
            if products:
                selected = st.multiselect("选择产品", 
                    options=[f"{p['name']}|{p['price']}" for p in products])
                
                items_data = []
                for item in selected:
                    name, price = item.split("|")
                    cols = st.columns([3, 1, 1])
                    with cols[0]:
                        st.write(f"📦 {name}")
                    with cols[1]:
                        qty = st.number_input("数量", min_value=1, value=1, key=f"qty_{item}")
                    with cols[2]:
                        st.write(f"¥{float(price) * qty:.2f}")
                    items_data.append({"Name": name, "price": float(price), "qty": qty})
            else:
                st.warning("请先添加产品")
                items_data = []
            
            if st.form_submit_button("生成送货单"):
                if client_name and items_data:
                    total = sum(item["price"] * item["qty"] for item in items_data)
                    delivery_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
                    
                    delivery = {
                        "id": delivery_id,
                        "client_name": client_name,
                        "delivery_date": str(delivery_date),
                        "total": float(total),
                        "remark": remark,
                        "status": "unpaid"
                    }
                    
                    if supabase_insert("deliveries", delivery):
                        for item in items_data:
                            item_rec = {
                                "delivery_id": delivery_id,
                                "product_name": item["Name"],
                                "price": item["price"],
                                "qty": item["qty"],
                                "subtotal": item["price"] * item["qty"]
                            }
                            supabase_insert("delivery_items", item_rec)
                        
                        st.success("✅ 送货单创建成功！")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("请选择客户和产品")
    
    st.markdown("### 送货单列表")
    deliveries = load_deliveries()
    payments = load_payments()
    
    if deliveries:
        filter_client = st.selectbox("筛选客户", 
            options=["全部"] + [c["name"] for c in clients])
        
        filtered = deliveries if filter_client == "全部" else [d for d in deliveries if d.get("client_name") == filter_client]
        
        for d in filtered:
            items = load_delivery_items(d["id"])
            paid = sum(p["amount"] for p in payments if p.get("delivery_id") == d["id"])
            
            with st.expander(f"📋 #{d['id'][:8]} | {d['delivery_date']} | {d['client_name']} | ¥{d['total']:.2f}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**客户：** {d['client_name']}")
                    st.write(f"**备注：** {d.get('remark') or '无'}")
                    
                    if items:
                        items_df = pd.DataFrame(items)
                        items_df = items_df[["product_name", "qty", "price", "subtotal"]]
                        items_df.columns = ["产品", "数量", "单价", "小计"]
                        st.table(items_df)
                
                with col2:
                    st.metric("总金额", f"¥{d['total']:.2f}")
                    status = d.get("status", "unpaid")
                    status_text = {"unpaid": "❌ 未付款", "partial": "⚠️ 部分付款", "paid": "✅ 已结清"}
                    st.write(status_text.get(status, status))
                    st.write(f"已付：¥{paid:.2f}")
                    st.write(f"欠款：¥{d['total'] - paid:.2f}")
    else:
        st.info("暂无送货单")

# ============ 打款记录 ============
def render_payment_page():
    st.markdown("## 💰 打款记录")
    clients = load_clients()
    
    with st.expander("➕ 记录打款", expanded=False):
        with st.form("add_payment"):
            col1, col2, col3 = st.columns(3)
            with col1:
                client_name = st.selectbox("选择客户 *",
                    options=[""] + [c["name"] for c in clients], index=0)
            with col2:
                payment_date = st.date_input("付款日期", value=date.today())
            with col3:
                amount = st.number_input("付款金额 *", min_value=0.0, step=100.0, format="%.2f")
            
            remark = st.text_input("备注", placeholder="付款方式说明")
            
            if st.form_submit_button("保存打款记录"):
                if client_name and amount > 0:
                    new_payment = {
                        "id": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
                        "client_name": client_name,
                        "payment_date": str(payment_date),
                        "amount": float(amount),
                        "remark": remark
                    }
                    if supabase_insert("payments", new_payment):
                        st.success("✅ 打款记录保存成功！")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("请选择客户并输入付款金额")
    
    st.markdown("### 付款记录")
    payments = load_payments()
    if payments:
        df = pd.DataFrame(payments)
        cols = [c for c in ["payment_date", "client_name", "amount", "remark"] if c in df.columns]
        df_display = df[cols].copy()
        df_display.columns = ["日期", "客户", "金额", "备注"]
        df_display["金额"] = df_display["金额"].apply(lambda x: f"¥{float(x):.2f}")
        st.dataframe(df_display, use_container_width=True)
        
        total = sum(p["amount"] for p in payments)
        st.metric("💵 总付款额", f"¥{total:.2f}")
    else:
        st.info("暂无打款记录")

# ============ 对账汇总 ============
def render_reconciliation_page():
    st.markdown("## 📊 对账汇总")
    clients = load_clients()
    deliveries = load_deliveries()
    payments = load_payments()
    
    summary = {}
    for client in clients:
        cname = client["name"]
        receivable = sum(d["total"] for d in deliveries if d.get("client_name") == cname)
        paid = sum(p["amount"] for p in payments if p.get("client_name") == cname)
        owed = receivable - paid
        
        summary[cname] = {
            "receivable": receivable,
            "paid": paid,
            "owed": owed,
            "status": "✅ 已结清" if owed <= 0 else "🔴 待收款"
        }
    
    if summary:
        df = pd.DataFrame([
            {"客户": k, "应收": f"¥{v['receivable']:.2f}", 
             "已收": f"¥{v['paid']:.2f}", "欠款": f"¥{v['owed']:.2f}", "状态": v['status']}
            for k, v in summary.items()
        ])
        st.dataframe(df, use_container_width=True)
        
        total_r = sum(v["receivable"] for v in summary.values())
        total_p = sum(v["paid"] for v in summary.values())
        total_o = sum(v["owed"] for v in summary.values())
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📦 总应收", f"¥{total_r:.2f}")
        with col2:
            st.metric("💰 总已收", f"¥{total_p:.2f}")
        with col3:
            st.metric("🔴 总欠款", f"¥{total_o:.2f}")
    else:
        st.info("暂无数据")
    
    st.markdown("### 📄 详细对账单")
    if clients:
        selected = st.selectbox("选择客户", options=[c["name"] for c in clients], key="detail_client")
        
        client_deliveries = [d for d in deliveries if d.get("client_name") == selected]
        client_payments = [p for p in payments if p.get("client_name") == selected]
        
        if client_deliveries:
            st.markdown(f"#### 📦 {selected} 的送货明细")
            
            for d in sorted(client_deliveries, key=lambda x: x["delivery_date"], reverse=True):
                paid = sum(p["amount"] for p in client_payments if p.get("delivery_id") == d["id"])
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"#{d['id'][:8]} | {d['delivery_date']}")
                with col2:
                    st.write(f"已付: ¥{paid:.2f}")
                with col3:
                    st.write(f"**¥{d['total']:.2f}**")
            
            total_r = sum(d["total"] for d in client_deliveries)
            total_p = sum(p["amount"] for p in client_payments)
            owed = total_r - total_p
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**应收合计：¥{total_r:.2f}**")
            with col2:
                if owed > 0:
                    st.markdown(f"**🔴 尚欠款：¥{owed:.2f}**")
                else:
                    st.markdown(f"**✅ 已结清**")
        else:
            st.info("该客户暂无送货记录")

# ============ 上游供应链管理 ============
def render_supply_chain_page():
    st.markdown("## 🏭 上游供应链管理")
    
    suppliers = load_suppliers()
    
    # 选择供应商或新增
    col1, col2 = st.columns([3, 1])
    with col1:
        if suppliers:
            selected = st.selectbox("选择供应商", 
                options=[""] + [s["name"] for s in suppliers], 
                key="supplier_select")
        else:
            st.info("暂无供应商，请先添加")
            selected = ""
    with col2:
        st.markdown("")  # 占位
        st.markdown("")
        if st.button("➕ 添加供应商", use_container_width=True):
            st.session_state["show_add_supplier"] = True
    
    # 添加供应商表单
    if st.session_state.get("show_add_supplier", False):
        with st.expander("➕ 添加新供应商", expanded=True):
            with st.form("add_supplier", clear_on_submit=True):
                st.markdown("### 📋 基本信息")
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("单位名称 *", placeholder="输入供应商名称")
                    address = st.text_input("地址", placeholder="输入详细地址")
                    legal_person = st.text_input("法人", placeholder="输入法人姓名")
                with col2:
                    phone = st.text_input("电话", placeholder="输入联系电话")
                    credit_code = st.text_input("统一社会信用代码", placeholder="18位统一社会信用代码")
                    business_desc = st.text_input("相关业务", placeholder="主营业务描述")
                
                col3, col4 = st.columns(2)
                with col3:
                    bank_name = st.text_input("开户银行", placeholder="开户银行名称")
                with col4:
                    bank_account = st.text_input("银行账号", placeholder="银行账号")
                
                if st.form_submit_button("💾 保存供应商"):
                    if name:
                        supplier_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
                        new_supplier = {
                            "id": supplier_id,
                            "name": name,
                            "address": address,
                            "legal_person": legal_person,
                            "phone": phone,
                            "credit_code": credit_code,
                            "bank_name": bank_name,
                            "bank_account": bank_account,
                            "business_desc": business_desc
                        }
                        if supabase_insert("suppliers", new_supplier):
                            st.success("✅ 供应商添加成功！")
                            st.session_state["show_add_supplier"] = False
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ 添加失败，请确保已在 Supabase 创建表")
                    else:
                        st.error("请输入单位名称")
                
                if st.button("取消", key="cancel_add_supplier"):
                    st.session_state["show_add_supplier"] = False
                    st.rerun()
    
    # 供应商详情
    if selected:
        supplier = next((s for s in suppliers if s["name"] == selected), None)
        if supplier:
            st.markdown("---")
            st.markdown(f"### 📋 {supplier['name']} - 基本信息")
            
            # 基本信息卡片
            info_cols = {
                "单位名称": supplier.get("name", "-"),
                "地址": supplier.get("address", "-"),
                "法人": supplier.get("legal_person", "-"),
                "电话": supplier.get("phone", "-"),
                "统一社会信用代码": supplier.get("credit_code", "-"),
                "开户银行": supplier.get("bank_name", "-"),
                "银行账号": supplier.get("bank_account", "-"),
                "相关业务": supplier.get("business_desc", "-")
            }
            
            # 显示为两列布局
            items = list(info_cols.items())
            mid = len(items) // 2
            col1, col2 = st.columns(2)
            for i, (key, val) in enumerate(items):
                with col1 if i < mid else col2:
                    st.text_input(f"📌 {key}", value=val, disabled=True, key=f"info_{key}")
            
            # 人员信息标签页
            st.markdown("---")
            st.markdown("### 👥 人员信息")
            
            contacts = load_supplier_contacts(supplier["id"])
            
            with st.expander("➕ 添加人员", expanded=False):
                with st.form(f"add_contact_{supplier['id']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        c_name = st.text_input("姓名 *", placeholder="人员姓名")
                        c_position = st.text_input("职务", placeholder="如：采购经理")
                    with c2:
                        c_phone = st.text_input("联系电话", placeholder="手机号码")
                        c_wechat = st.text_input("微信", placeholder="微信号")
                    
                    c_company = st.text_input("所属公司", placeholder="所属公司（可填供应商名称）")
                    c_remark = st.text_input("备注", placeholder="其他说明")
                    
                    if st.form_submit_button("💾 保存人员"):
                        if c_name:
                            new_contact = {
                                "id": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12],
                                "supplier_id": supplier["id"],
                                "name": c_name,
                                "position": c_position,
                                "company": c_company or supplier["name"],
                                "phone": c_phone,
                                "wechat": c_wechat,
                                "remark": c_remark
                            }
                            if supabase_insert("supplier_contacts", new_contact):
                                st.success("✅ 人员添加成功！")
                                st.cache_data.clear()
                                st.rerun()
                        else:
                            st.error("请输入姓名")
            
            if contacts:
                contacts_df = pd.DataFrame(contacts)
                display_cols = ["name", "position", "company", "phone", "wechat", "remark"]
                available = [c for c in display_cols if c in contacts_df.columns]
                contacts_df = contacts_df[available].copy()
                contacts_df.columns = ["姓名", "职务", "所属公司", "电话", "微信", "备注"]
                st.dataframe(contacts_df, use_container_width=True)
            else:
                st.info("暂无人员信息")
            
            # 物料信息标签页
            st.markdown("---")
            st.markdown("### 📦 相关物料")
            
            materials = load_supplier_materials(supplier["id"])
            
            with st.expander("➕ 添加物料", expanded=False):
                with st.form(f"add_material_{supplier['id']}"):
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        m_name = st.text_input("物料名称 *", placeholder="物料名称")
                        m_spec = st.text_input("规格", placeholder="规格型号")
                    with m2:
                        m_unit = st.text_input("单位", placeholder="如：个、米、吨")
                        m_price_excl = st.number_input("不含税单价", min_value=0.0, step=0.01, format="%.2f")
                    with m3:
                        m_tax_rate = st.selectbox("税率", options=[0.13, 0.09, 0.06, 0.03, 0.0], index=0, format_func=lambda x: f"{x*100:.0f}%")
                        m_incl_tax = st.number_input("含税单价", min_value=0.0, step=0.01, format="%.2f", value=m_price_excl * (1 + m_tax_rate))
                    
                    m_freight = st.selectbox("是否含运", options=["否", "是"])
                    m_remark = st.text_input("备注", placeholder="其他说明")
                    
                    if st.form_submit_button("💾 保存物料"):
                        if m_name:
                            new_material = {
                                "id": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12],
                                "supplier_id": supplier["id"],
                                "name": m_name,
                                "spec": m_spec,
                                "unit": m_unit,
                                "price_excl_tax": float(m_price_excl),
                                "tax_rate": float(m_tax_rate),
                                "price_incl_tax": float(m_incl_tax),
                                "includes_freight": m_freight,
                                "remark": m_remark
                            }
                            if supabase_insert("supplier_materials", new_material):
                                st.success("✅ 物料添加成功！")
                                st.cache_data.clear()
                                st.rerun()
                        else:
                            st.error("请输入物料名称")
            
            if materials:
                materials_df = pd.DataFrame(materials)
                display_cols = ["name", "spec", "unit", "price_excl_tax", "tax_rate", "price_incl_tax", "includes_freight", "remark"]
                available = [c for c in display_cols if c in materials_df.columns]
                materials_df = materials_df[available].copy()
                materials_df.columns = ["物料名称", "规格", "单位", "不含税单价", "税率", "含税单价", "含运", "备注"]
                # 格式化显示
                materials_df["不含税单价"] = materials_df["不含税单价"].apply(lambda x: f"¥{float(x):.2f}")
                materials_df["含税单价"] = materials_df["含税单价"].apply(lambda x: f"¥{float(x):.2f}")
                materials_df["税率"] = materials_df["税率"].apply(lambda x: f"{float(x)*100:.0f}%")
                st.dataframe(materials_df, use_container_width=True)
            else:
                st.info("暂无物料信息")
    
    # 供应商总览
    if suppliers:
        st.markdown("---")
        st.markdown("### 📊 供应商总览")
        
        overview_cols = ["name", "legal_person", "phone", "business_desc"]
        df = pd.DataFrame(suppliers)
        available = [c for c in overview_cols if c in df.columns]
        if available:
            df_overview = df[available].copy()
            df_overview.columns = ["单位名称", "法人", "电话", "相关业务"]
            st.dataframe(df_overview, use_container_width=True)
        
        st.markdown(f"**共 {len(suppliers)} 家供应商**")


# ============ 主程序 ============
def main():
    init_auth_state()
    
    if not st.session_state.authenticated:
        render_login_page()
    else:
        page = render_sidebar()
        
        if page == "客户":
            render_client_page()
        elif page == "产品":
            render_product_page()
        elif page == "送货单":
            render_delivery_page()
        elif page == "打款":
            render_payment_page()
        elif page == "对账":
            render_reconciliation_page()
        elif page == "供应链":
            render_supply_chain_page()
        elif page == "用户管理":
            render_user_management_page()

if __name__ == "__main__":
    main()
