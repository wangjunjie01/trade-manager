"""
贸易公司内部管理系统 - MVP (Supabase版 + 用户登录)
送货单管理 & 对账系统
所有功能：弹窗新增/编辑、批量操作、导入导出
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
import hashlib
import io
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
    # 弹窗状态初始化
    if "modal_state" not in st.session_state:
        st.session_state.modal_state = {}
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = {}

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

def supabase_update(table, data, filters):
    """更新数据"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    try:
        resp = requests.patch(url, headers=HEADERS, params=filters, json=data)
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

def supabase_batch_delete(table, ids, id_field="id"):
    """批量删除"""
    success = True
    for id_val in ids:
        if not supabase_delete(table, {f"{id_field}=eq.{id_val}"}):
            success = False
    return success

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
[data-testid="stHorizontalBlock"] { gap: 1rem; }
</style>
""", unsafe_allow_html=True)

# ============ 通用组件 ============
def render_action_buttons(table_name, row_id, on_edit_key=None, on_delete_callback=None):
    """渲染操作按钮（编辑、删除）"""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ 编辑", key=f"edit_{table_name}_{row_id}", use_container_width=True):
            st.session_state.modal_state[f"edit_{table_name}"] = row_id
            st.rerun()
    with col2:
        if st.button("🗑️ 删除", key=f"del_{table_name}_{row_id}", use_container_width=True):
            st.session_state.confirm_delete[f"{table_name}_{row_id}"] = True

def render_batch_actions(table_name, df, id_field="id", extra_cols=None):
    """渲染批量操作栏"""
    col_select, col_count, col_actions = st.columns([1, 1, 4])

    with col_select:
        if df is not None and len(df) > 0:
            all_selected = st.checkbox("全选", key=f"select_all_{table_name}")

    with col_count:
        if df is not None and len(df) > 0:
            selected_count = len(df[df.get("_selected", False)])
            st.caption(f"已选: {selected_count} 项")

    with col_actions:
        if df is not None and len(df) > 0:
            sel_cols = st.columns([1, 1, 1])
            with sel_cols[0]:
                if st.button("📥 导出选中", key=f"export_sel_{table_name}", use_container_width=True):
                    selected_df = df[df.get("_selected", False)]
                    if len(selected_df) > 0:
                        export_to_csv(selected_df, f"{table_name}_selected.csv")
            with sel_cols[1]:
                if st.button("📥 导出全部", key=f"export_all_{table_name}", use_container_width=True):
                    export_to_csv(df, f"{table_name}_all.csv")
            with sel_cols[2]:
                if st.button("🗑️ 删除选中", key=f"delete_sel_{table_name}", use_container_width=True):
                    selected_ids = df[df.get("_selected", False)][id_field].tolist()
                    if selected_ids:
                        st.session_state.confirm_delete[f"batch_{table_name}"] = selected_ids

def export_to_csv(df, filename):
    """导出数据为CSV"""
    if df is not None and len(df) > 0:
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label=f"📥 下载 {filename}",
            data=csv,
            file_name=filename,
            mime="text/csv",
            key=f"download_{filename}"
        )
        st.success(f"✅ 已生成 {filename}")

def import_csv_modal(table_name, required_cols, on_import):
    """导入CSV弹窗"""
    if st.button(f"📤 导入 {table_name}", type="secondary"):
        st.session_state.modal_state[f"import_{table_name}"] = True

    if st.session_state.get(f"import_{table_name}"):
        st.markdown("### 📤 导入数据")
        st.info(f"必填字段: {', '.join(required_cols)}")

        uploaded_file = st.file_uploader("选择 CSV 文件", type=["csv"])

        if uploaded_file:
            try:
                df_upload = pd.read_csv(uploaded_file)

                # 检查必填字段
                missing_cols = [c for c in required_cols if c not in df_upload.columns]
                if missing_cols:
                    st.error(f"❌ 缺少必填字段: {', '.join(missing_cols)}")
                else:
                    st.markdown("#### 预览数据")
                    st.dataframe(df_upload.head(10), use_container_width=True)

                    if st.button("✅ 确认导入", key=f"confirm_import_{table_name}"):
                        count = on_import(df_upload)
                        if count > 0:
                            st.success(f"✅ 成功导入 {count} 条数据")
                            st.cache_data.clear()
                            st.session_state.modal_state[f"import_{table_name}"] = False
                            st.rerun()
                        else:
                            st.error("❌ 导入失败")
            except Exception as e:
                st.error(f"❌ 读取文件失败: {str(e)}")

        if st.button("取消", key=f"cancel_import_{table_name}"):
            st.session_state.modal_state[f"import_{table_name}"] = False
            st.rerun()

def confirm_delete_modal(key, item_name, on_confirm):
    """删除确认弹窗"""
    if st.session_state.get(f"confirm_delete_{key}"):
        st.warning(f"⚠️ 确定要删除「{item_name}」吗？此操作不可恢复！")

        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("✅ 确认删除", type="primary", key=f"confirm_{key}"):
                on_confirm()
                st.session_state.confirm_delete[key] = False
                st.session_state.modal_state[f"confirm_delete_{key}"] = False
                st.cache_data.clear()
                st.success("✅ 删除成功")
                st.rerun()
        with col_cancel:
            if st.button("❌ 取消", key=f"cancel_{key}"):
                st.session_state.confirm_delete[key] = False
                st.rerun()

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

    clients = load_clients()
    df_clients = pd.DataFrame(clients) if clients else pd.DataFrame()

    # 操作栏
    col_add, col_import, col_export = st.columns([1, 1, 1])
    with col_add:
        if st.button("➕ 添加客户", type="primary", use_container_width=True):
            st.session_state.modal_state["add_client"] = True
    with col_import:
        import_csv_modal("clients", ["name"], import_clients)
    with col_export:
        if st.button("📥 导出全部", use_container_width=True):
            export_to_csv(df_clients, "clients.csv")

    st.markdown("---")

    # 客户列表
    if clients:
        # 选择列
        display_cols = ["name", "contact", "phone", "address"]
        available_cols = [c for c in display_cols if c in df_clients.columns]
        df_display = df_clients[available_cols].copy()
        df_display.columns = ["客户名称", "联系人", "电话", "地址"]

        # 添加选择列
        df_display["_selected"] = False

        # 渲染表格（带选择框）
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "_selected": st.column_config.CheckboxColumn("选择")
            },
            disabled=["客户名称", "联系人", "电话", "地址"]
        )

        # 批量操作
        selected_count = edited_df["_selected"].sum()
        if selected_count > 0:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button(f"📥 导出选中 ({selected_count})", use_container_width=True):
                    export_to_csv(edited_df[edited_df["_selected"]], "clients_selected.csv")
            with col2:
                if st.button(f"🗑️ 删除选中 ({selected_count})", use_container_width=True):
                    selected_names = edited_df[edited_df["_selected"]]["客户名称"].tolist()
                    st.session_state.confirm_delete["batch_clients"] = selected_names

            # 批量删除确认
            if st.session_state.get("confirm_delete", {}).get("batch_clients"):
                names = st.session_state.confirm_delete["batch_clients"]
                st.warning(f"⚠️ 确定要删除以下 {len(names)} 个客户吗？\n" + "\n".join([f"- {n}" for n in names[:5]]))
                if len(names) > 5:
                    st.caption(f"... 还有 {len(names) - 5} 个")
                col_conf, col_can = st.columns(2)
                with col_conf:
                    if st.button("✅ 确认删除", type="primary"):
                        for name in names:
                            client = next((c for c in clients if c.get("name") == name), None)
                            if client:
                                supabase_delete("clients", {"id=eq." + client.get("id", "")})
                        st.session_state.confirm_delete["batch_clients"] = False
                        st.cache_data.clear()
                        st.success(f"✅ 已删除 {len(names)} 个客户")
                        st.rerun()
                with col_can:
                    if st.button("❌ 取消"):
                        st.session_state.confirm_delete["batch_clients"] = False
                        st.rerun()
    else:
        st.info("暂无客户")

    # 添加/编辑客户弹窗
    render_client_modal(clients)

def render_client_modal(existing_clients):
    """客户新增/编辑弹窗"""
    modal_key = "add_client"
    edit_key = st.session_state.modal_state.get("edit_client")

    # 打开弹窗
    if st.session_state.get(modal_key) or edit_key:
        with st.container():
            st.markdown("""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
                background-color: #f0f8ff;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #b8daff;
            }
            </style>
            """, unsafe_allow_html=True)

            is_edit = edit_key is not None
            edit_data = None
            if is_edit:
                edit_data = next((c for c in existing_clients if c.get("id") == edit_key), None)
                st.markdown(f"### ✏️ 编辑客户")
            else:
                st.markdown("### ➕ 添加客户")

            with st.form(f"client_form_{modal_key}", clear_on_submit=not is_edit):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("客户名称 *", placeholder="必填",
                                        value=edit_data.get("name", "") if edit_data else "")
                with c2:
                    contact = st.text_input("联系人",
                                           value=edit_data.get("contact", "") if edit_data else "")

                c3, c4 = st.columns(2)
                with c3:
                    phone = st.text_input("电话",
                                        value=edit_data.get("phone", "") if edit_data else "")
                with c4:
                    address = st.text_input("地址",
                                          value=edit_data.get("address", "") if edit_data else "")

                col_save, col_close = st.columns(2)
                with col_save:
                    submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)
                with col_close:
                    closed = st.form_submit_button("关闭", use_container_width=True)

                if closed:
                    st.session_state.modal_state[modal_key] = False
                    if "edit_client" in st.session_state.modal_state:
                        del st.session_state.modal_state["edit_client"]
                    st.rerun()

                if submitted:
                    if not name:
                        st.error("❌ 客户名称不能为空")
                    else:
                        data = {
                            "name": name,
                            "contact": contact or "",
                            "phone": phone or "",
                            "address": address or ""
                        }

                        if is_edit and edit_data:
                            if supabase_update("clients", data, {"id=eq." + edit_key}):
                                st.success("✅ 客户更新成功！")
                            else:
                                st.error("❌ 更新失败")
                        else:
                            data["id"] = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
                            if supabase_insert("clients", data):
                                st.success("✅ 客户添加成功！")
                            else:
                                st.error("❌ 添加失败")

                        st.session_state.modal_state[modal_key] = False
                        if "edit_client" in st.session_state.modal_state:
                            del st.session_state.modal_state["edit_client"]
                        st.cache_data.clear()
                        st.rerun()

def import_clients(df):
    """导入客户数据"""
    count = 0
    for _, row in df.iterrows():
        client_data = {
            "id": hashlib.md5(str(datetime.now() + str(count)).encode()).hexdigest()[:8],
            "name": row.get("name", ""),
            "contact": row.get("contact", "") or "",
            "phone": row.get("phone", "") or "",
            "address": row.get("address", "") or ""
        }
        if client_data["name"] and supabase_insert("clients", client_data):
            count += 1
    return count

# ============ 产品管理 ============
def render_product_page():
    st.markdown("## 📦 产品管理")

    products = load_products()
    df_products = pd.DataFrame(products) if products else pd.DataFrame()

    # 操作栏
    col_add, col_import, col_export = st.columns([1, 1, 1])
    with col_add:
        if st.button("➕ 添加产品", type="primary", use_container_width=True):
            st.session_state.modal_state["add_product"] = True
    with col_import:
        import_csv_modal("products", ["name"], import_products)
    with col_export:
        if st.button("📥 导出全部", use_container_width=True):
            export_to_csv(df_products, "products.csv")

    st.markdown("---")

    # 产品列表
    if products:
        display_cols = ["name", "spec", "price", "stock"]
        available_cols = [c for c in display_cols if c in df_products.columns]
        df_display = df_products[available_cols].copy()
        df_display.columns = ["产品名称", "规格", "单价(元)", "库存"]
        df_display["_selected"] = False

        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "_selected": st.column_config.CheckboxColumn("选择")
            },
            disabled=["产品名称", "规格", "单价(元)", "库存"]
        )

        # 批量操作
        selected_count = edited_df["_selected"].sum()
        if selected_count > 0:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button(f"📥 导出选中 ({selected_count})", use_container_width=True):
                    export_to_csv(edited_df[edited_df["_selected"]], "products_selected.csv")
            with col2:
                if st.button(f"🗑️ 删除选中 ({selected_count})", use_container_width=True):
                    selected_names = edited_df[edited_df["_selected"]]["产品名称"].tolist()
                    st.session_state.confirm_delete["batch_products"] = selected_names

            # 批量删除确认
            if st.session_state.get("confirm_delete", {}).get("batch_products"):
                names = st.session_state.confirm_delete["batch_products"]
                st.warning(f"⚠️ 确定要删除以下 {len(names)} 个产品吗？\n" + "\n".join([f"- {n}" for n in names[:5]]))
                if len(names) > 5:
                    st.caption(f"... 还有 {len(names) - 5} 个")
                col_conf, col_can = st.columns(2)
                with col_conf:
                    if st.button("✅ 确认删除", type="primary"):
                        for name in names:
                            product = next((p for p in products if p.get("name") == name), None)
                            if product:
                                supabase_delete("products", {"id=eq." + product.get("id", "")})
                        st.session_state.confirm_delete["batch_products"] = False
                        st.cache_data.clear()
                        st.success(f"✅ 已删除 {len(names)} 个产品")
                        st.rerun()
                with col_can:
                    if st.button("❌ 取消"):
                        st.session_state.confirm_delete["batch_products"] = False
                        st.rerun()
    else:
        st.info("暂无产品")

    render_product_modal(products)

def render_product_modal(existing_products):
    """产品新增/编辑弹窗"""
    modal_key = "add_product"
    edit_key = st.session_state.modal_state.get("edit_product")

    if st.session_state.get(modal_key) or edit_key:
        with st.container():
            st.markdown("""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
                background-color: #f0fff0;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #98d89b;
            }
            </style>
            """, unsafe_allow_html=True)

        is_edit = edit_key is not None
        edit_data = None
        if is_edit:
            edit_data = next((p for p in existing_products if p.get("id") == edit_key), None)
            st.markdown("### ✏️ 编辑产品")
        else:
            st.markdown("### ➕ 添加产品")

        with st.form(f"product_form_{modal_key}", clear_on_submit=not is_edit):
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input("产品名称 *", placeholder="必填",
                                    value=edit_data.get("name", "") if edit_data else "")
            with c2:
                spec = st.text_input("规格型号",
                                    value=edit_data.get("spec", "") if edit_data else "")
            with c3:
                price = st.number_input("单价 (元)", min_value=0.0, step=0.01, format="%.2f",
                                       value=float(edit_data.get("price", 0)) if edit_data else 0.0)

            col_save, col_close = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)
            with col_close:
                closed = st.form_submit_button("关闭", use_container_width=True)

            if closed:
                st.session_state.modal_state[modal_key] = False
                if "edit_product" in st.session_state.modal_state:
                    del st.session_state.modal_state["edit_product"]
                st.rerun()

            if submitted:
                if not name:
                    st.error("❌ 产品名称不能为空")
                else:
                    data = {
                        "name": name,
                        "spec": spec or "",
                        "price": float(price),
                        "stock": int(edit_data.get("stock", 0)) if edit_data else 0
                    }

                    if is_edit and edit_data:
                        if supabase_update("products", data, {"id=eq." + edit_key}):
                            st.success("✅ 产品更新成功！")
                        else:
                            st.error("❌ 更新失败")
                    else:
                        data["id"] = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
                        if supabase_insert("products", data):
                            st.success("✅ 产品添加成功！")
                        else:
                            st.error("❌ 添加失败")

                    st.session_state.modal_state[modal_key] = False
                    if "edit_product" in st.session_state.modal_state:
                        del st.session_state.modal_state["edit_product"]
                    st.cache_data.clear()
                    st.rerun()

def import_products(df):
    """导入产品数据"""
    count = 0
    for _, row in df.iterrows():
        product_data = {
            "id": hashlib.md5(str(datetime.now() + str(count)).encode()).hexdigest()[:8],
            "name": row.get("name", ""),
            "spec": row.get("spec", "") or "",
            "price": float(row.get("price", 0)),
            "stock": int(row.get("stock", 0))
        }
        if product_data["name"] and supabase_insert("products", product_data):
            count += 1
    return count

# ============ 送货单管理 ============
def render_delivery_page():
    st.markdown("## 📋 送货单管理")
    clients = load_clients()
    products = load_products()
    deliveries = load_deliveries()

    # 操作栏
    col_add, col_export = st.columns([1, 1])
    with col_add:
        if st.button("➕ 创建送货单", type="primary", use_container_width=True):
            st.session_state.modal_state["add_delivery"] = True
    with col_export:
        df_deliveries = pd.DataFrame(deliveries) if deliveries else pd.DataFrame()
        if st.button("📥 导出全部", use_container_width=True):
            export_to_csv(df_deliveries, "deliveries.csv")

    st.markdown("---")

    # 送货单列表
    if deliveries:
        for d in deliveries:
            items = load_delivery_items(d["id"])
            col1, col2, col3 = st.columns([5, 1, 1])

            with col1:
                status = d.get("status", "unpaid")
                status_emoji = {"unpaid": "❌", "partial": "⚠️", "paid": "✅"}.get(status, "")
                st.markdown(f"**#{d['id'][:8]}** | {d['delivery_date']} | {d['client_name']} | {status_emoji} ¥{d['total']:.2f}")

            with col2:
                if st.button("📋 详情", key=f"view_{d['id']}"):
                    st.session_state.modal_state[f"view_delivery_{d['id']}"] = True

            with col3:
                if st.button("🗑️", key=f"del_d_{d['id']}", help="删除"):
                    st.session_state.confirm_delete[f"delivery_{d['id']}"] = True

            # 删除确认
            if st.session_state.confirm_delete.get(f"delivery_{d['id']}"):
                st.warning(f"⚠️ 确定删除送货单 #{d['id'][:8]} 吗？")
                col_c, col_ca = st.columns(2)
                with col_c:
                    if st.button("✅ 确认", type="primary", key=f"confirm_delivery_{d['id']}"):
                        # 删除明细
                        for item in items:
                            supabase_delete("delivery_items", {"id=eq." + item.get("id", "")})
                        # 删除主单
                        supabase_delete("deliveries", {"id=eq." + d["id"]})
                        st.session_state.confirm_delete[f"delivery_{d['id']}"] = False
                        st.cache_data.clear()
                        st.success("✅ 删除成功")
                        st.rerun()
                with col_ca:
                    if st.button("❌ 取消", key=f"cancel_delivery_{d['id']}"):
                        st.session_state.confirm_delete[f"delivery_{d['id']}"] = False
                        st.rerun()

            # 详情弹窗
            if st.session_state.modal_state.get(f"view_delivery_{d['id']}"):
                with st.expander("📋 送货单详情", expanded=True):
                    st.markdown(f"**客户：** {d['client_name']}")
                    st.markdown(f"**日期：** {d['delivery_date']}")
                    st.markdown(f"**备注：** {d.get('remark') or '无'}")
                    if items:
                        items_df = pd.DataFrame(items)
                        items_df = items_df[["product_name", "qty", "price", "subtotal"]]
                        items_df.columns = ["产品", "数量", "单价", "小计"]
                        st.table(items_df)
                    st.markdown(f"**总金额：¥{d['total']:.2f}**")
                    if st.button("关闭", key=f"close_view_{d['id']}"):
                        st.session_state.modal_state[f"view_delivery_{d['id']}"] = False
                        st.rerun()

            st.divider()
    else:
        st.info("暂无送货单")

    # 新增送货单弹窗
    render_delivery_modal(clients, products)

def render_delivery_modal(clients, products):
    """送货单新增弹窗"""
    if st.session_state.get("add_delivery"):
        with st.container():
            st.markdown("""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
                background-color: #fff8f0;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #ffd89b;
            }
            </style>
            """, unsafe_allow_html=True)

        st.markdown("### ➕ 创建送货单")

        with st.form("add_delivery_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                client_options = [""] + [c["name"] for c in clients]
                client_name = st.selectbox("选择客户 *", options=client_options, index=0)
            with c2:
                delivery_date = st.date_input("送货日期", value=date.today())

            remark = st.text_input("备注", placeholder="可选备注信息")

            if products:
                selected_items = st.multiselect("选择产品",
                    options=[f"{p['name']}|{p['price']}" for p in products])

                items_data = []
                for item in selected_items:
                    name, price = item.split("|")
                    cols = st.columns([3, 1, 1])
                    with cols[0]:
                        st.write(f"📦 {name}")
                    with cols[1]:
                        qty = st.number_input("数量", min_value=1, value=1,
                                             key=f"qty_{item}", label_visibility="collapsed")
                    with cols[2]:
                        st.write(f"¥{float(price) * qty:.2f}")
                    items_data.append({"name": name, "price": float(price), "qty": qty})
            else:
                st.warning("请先添加产品")
                items_data = []

            col_save, col_close = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 生成送货单", type="primary", use_container_width=True)
            with col_close:
                closed = st.form_submit_button("关闭", use_container_width=True)

            if closed:
                st.session_state.modal_state["add_delivery"] = False
                st.rerun()

            if submitted:
                if not client_name:
                    st.error("❌ 请选择客户")
                elif not items_data:
                    st.error("❌ 请选择至少一个产品")
                else:
                    total = sum(item["price"] * item["qty"] for item in items_data)
                    delivery_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]

                    delivery = {
                        "id": delivery_id,
                        "client_name": client_name,
                        "delivery_date": str(delivery_date),
                        "total": float(total),
                        "remark": remark or "",
                        "status": "unpaid"
                    }

                    if supabase_insert("deliveries", delivery):
                        for item in items_data:
                            item_rec = {
                                "delivery_id": delivery_id,
                                "product_name": item["name"],
                                "price": item["price"],
                                "qty": item["qty"],
                                "subtotal": item["price"] * item["qty"]
                            }
                            supabase_insert("delivery_items", item_rec)

                        st.success("✅ 送货单创建成功！")
                        st.session_state.modal_state["add_delivery"] = False
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 创建失败")

# ============ 打款记录 ============
def render_payment_page():
    st.markdown("## 💰 打款记录")
    clients = load_clients()
    payments = load_payments()
    df_payments = pd.DataFrame(payments) if payments else pd.DataFrame()

    # 操作栏
    col_add, col_import, col_export = st.columns([1, 1, 1])
    with col_add:
        if st.button("➕ 记录打款", type="primary", use_container_width=True):
            st.session_state.modal_state["add_payment"] = True
    with col_import:
        import_csv_modal("payments", ["client_name", "amount"], import_payments)
    with col_export:
        if st.button("📥 导出全部", use_container_width=True):
            export_to_csv(df_payments, "payments.csv")

    st.markdown("---")

    # 打款列表
    if payments:
        display_cols = ["payment_date", "client_name", "amount", "remark"]
        available_cols = [c for c in display_cols if c in df_payments.columns]
        df_display = df_payments[available_cols].copy()
        df_display.columns = ["日期", "客户", "金额", "备注"]
        df_display["_selected"] = False

        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "_selected": st.column_config.CheckboxColumn("选择")
            },
            disabled=["日期", "客户", "金额", "备注"]
        )

        # 批量操作
        selected_count = edited_df["_selected"].sum()
        if selected_count > 0:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button(f"📥 导出选中 ({selected_count})", use_container_width=True):
                    export_to_csv(edited_df[edited_df["_selected"]], "payments_selected.csv")
            with col2:
                if st.button(f"🗑️ 删除选中 ({selected_count})", use_container_width=True):
                    # 通过日期+客户+金额定位记录
                    selected_records = edited_df[edited_df["_selected"]]
                    ids_to_delete = []
                    for _, row in selected_records.iterrows():
                        for p in payments:
                            if (str(p.get("payment_date", "")) == str(row["日期"]) and
                                p.get("client_name", "") == row["客户"] and
                                float(p.get("amount", 0)) == float(row["金额"].replace("¥", "").replace(",", ""))):
                                ids_to_delete.append(p.get("id"))
                                break
                    st.session_state.confirm_delete["batch_payments"] = ids_to_delete

            # 批量删除确认
            if st.session_state.get("confirm_delete", {}).get("batch_payments"):
                ids = st.session_state.confirm_delete["batch_payments"]
                st.warning(f"⚠️ 确定要删除以下 {len(ids)} 条打款记录吗？")
                col_conf, col_can = st.columns(2)
                with col_conf:
                    if st.button("✅ 确认删除", type="primary"):
                        for pid in ids:
                            supabase_delete("payments", {"id=eq." + pid})
                        st.session_state.confirm_delete["batch_payments"] = False
                        st.cache_data.clear()
                        st.success(f"✅ 已删除 {len(ids)} 条记录")
                        st.rerun()
                with col_can:
                    if st.button("❌ 取消"):
                        st.session_state.confirm_delete["batch_payments"] = False
                        st.rerun()

        # 统计
        total = sum(p["amount"] for p in payments)
        st.metric("💵 总付款额", f"¥{total:.2f}")
    else:
        st.info("暂无打款记录")

    render_payment_modal(clients, payments)

def render_payment_modal(clients, existing_payments):
    """打款新增/编辑弹窗"""
    modal_key = "add_payment"
    edit_key = st.session_state.modal_state.get("edit_payment")

    if st.session_state.get(modal_key) or edit_key:
        with st.container():
            st.markdown("""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
                background-color: #fff8f0;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #ffd89b;
            }
            </style>
            """, unsafe_allow_html=True)

        is_edit = edit_key is not None
        edit_data = None
        if is_edit:
            edit_data = next((p for p in existing_payments if p.get("id") == edit_key), None)
            st.markdown("### ✏️ 编辑打款记录")
        else:
            st.markdown("### ➕ 记录打款")

        with st.form(f"payment_form_{modal_key}", clear_on_submit=not is_edit):
            c1, c2, c3 = st.columns(3)
            with c1:
                client_options = [""] + [c["name"] for c in clients]
                default_idx = 0
                if edit_data and edit_data.get("client_name") in client_options:
                    default_idx = client_options.index(edit_data["client_name"])
                client_name = st.selectbox("选择客户 *", options=client_options, index=default_idx)
            with c2:
                payment_date = st.date_input("付款日期",
                                            value=datetime.strptime(edit_data.get("payment_date", date.today().isoformat()), "%Y-%m-%d").date() if edit_data else date.today())
            with c3:
                amount = st.number_input("付款金额 *", min_value=0.0, step=100.0, format="%.2f",
                                        value=float(edit_data.get("amount", 0)) if edit_data else 0.0)

            remark = st.text_input("备注",
                                  value=edit_data.get("remark", "") if edit_data else "",
                                  placeholder="付款方式说明")

            col_save, col_close = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)
            with col_close:
                closed = st.form_submit_button("关闭", use_container_width=True)

            if closed:
                st.session_state.modal_state[modal_key] = False
                if "edit_payment" in st.session_state.modal_state:
                    del st.session_state.modal_state["edit_payment"]
                st.rerun()

            if submitted:
                if not client_name:
                    st.error("❌ 请选择客户")
                elif amount <= 0:
                    st.error("❌ 请输入付款金额")
                else:
                    data = {
                        "client_name": client_name,
                        "payment_date": str(payment_date),
                        "amount": float(amount),
                        "remark": remark or ""
                    }

                    if is_edit and edit_data:
                        if supabase_update("payments", data, {"id=eq." + edit_key}):
                            st.success("✅ 打款记录更新成功！")
                        else:
                            st.error("❌ 更新失败")
                    else:
                        data["id"] = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
                        if supabase_insert("payments", data):
                            st.success("✅ 打款记录保存成功！")
                        else:
                            st.error("❌ 添加失败")

                    st.session_state.modal_state[modal_key] = False
                    if "edit_payment" in st.session_state.modal_state:
                        del st.session_state.modal_state["edit_payment"]
                    st.cache_data.clear()
                    st.rerun()

def import_payments(df):
    """导入打款记录"""
    count = 0
    for _, row in df.iterrows():
        payment_data = {
            "id": hashlib.md5(str(datetime.now() + str(count)).encode()).hexdigest()[:8],
            "client_name": row.get("client_name", ""),
            "payment_date": str(row.get("payment_date", date.today())),
            "amount": float(row.get("amount", 0)),
            "remark": row.get("remark", "") or ""
        }
        if payment_data["client_name"] and payment_data["amount"] > 0:
            if supabase_insert("payments", payment_data):
                count += 1
    return count

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
    """上游供应链管理主页面"""
    suppliers = load_suppliers()

    # 操作栏
    col_add, col_export = st.columns([1, 1])
    with col_add:
        if st.button("➕ 添加供应商", type="primary", use_container_width=True):
            st.session_state.modal_state["add_supplier"] = True
    with col_export:
        df_suppliers = pd.DataFrame(suppliers) if suppliers else pd.DataFrame()
        if st.button("📥 导出全部", use_container_width=True):
            export_to_csv(df_suppliers, "suppliers.csv")

    st.markdown("---")

    # 供应商选择
    if not suppliers:
        st.info("📭 暂无供应商，请点击上方「➕ 添加供应商」创建")
        st.session_state["selected_supplier"] = None
    else:
        supplier_names = [s["name"] for s in suppliers]
        default_idx = 0
        if st.session_state.get("selected_supplier") in supplier_names:
            default_idx = supplier_names.index(st.session_state["selected_supplier"])

        selected = st.selectbox("选择供应商", options=supplier_names, index=default_idx, key="supplier_select")
        st.session_state["selected_supplier"] = selected

    # 供应商详情
    if st.session_state.get("selected_supplier"):
        selected_name = st.session_state["selected_supplier"]
        supplier = next((s for s in suppliers if s["name"] == selected_name), None)

        if supplier:
            # 基本信息卡片
            with st.container():
                st.markdown("#### 📋 基本信息")

                cols = st.columns(3)
                with cols[0]:
                    st.text_input("单位名称", value=supplier.get("name", "-"), disabled=True)
                with cols[1]:
                    st.text_input("法人", value=supplier.get("legal_person", "-") or "-", disabled=True)
                with cols[2]:
                    st.text_input("电话", value=supplier.get("phone", "-") or "-", disabled=True)

                cols2 = st.columns(3)
                with cols2[0]:
                    st.text_input("地址", value=supplier.get("address", "-") or "-", disabled=True)
                with cols2[1]:
                    st.text_input("统一社会信用代码", value=supplier.get("credit_code", "-") or "-", disabled=True)
                with cols2[2]:
                    st.text_input("相关业务", value=supplier.get("business_desc", "-") or "-", disabled=True)

                cols3 = st.columns(2)
                with cols3[0]:
                    st.text_input("开户银行", value=supplier.get("bank_name", "-") or "-", disabled=True)
                with cols3[1]:
                    st.text_input("银行账号", value=supplier.get("bank_account", "-") or "-", disabled=True)

                # 编辑/删除按钮
                col_edit, col_del = st.columns([1, 1])
                with col_edit:
                    if st.button("✏️ 编辑供应商", use_container_width=True):
                        st.session_state.modal_state["edit_supplier"] = supplier["id"]
                with col_del:
                    if st.button("🗑️ 删除供应商", use_container_width=True):
                        st.session_state.confirm_delete[f"supplier_{supplier['id']}"] = True

                # 删除确认
                if st.session_state.confirm_delete.get(f"supplier_{supplier['id']}"):
                    st.warning(f"⚠️ 确定删除供应商「{supplier['name']}」吗？\n这将同时删除关联的人员和物料信息！")
                    col_c, col_ca = st.columns(2)
                    with col_c:
                        if st.button("✅ 确认删除", type="primary", key=f"confirm_sup_{supplier['id']}"):
                            # 删除关联数据
                            contacts = load_supplier_contacts(supplier["id"])
                            for c in contacts:
                                supabase_delete("supplier_contacts", {"id=eq." + c.get("id", "")})
                            materials = load_supplier_materials(supplier["id"])
                            for m in materials:
                                supabase_delete("supplier_materials", {"id=eq." + m.get("id", "")})
                            # 删除供应商
                            supabase_delete("suppliers", {"id=eq." + supplier["id"]})
                            st.session_state.confirm_delete[f"supplier_{supplier['id']}"] = False
                            st.cache_data.clear()
                            st.success("✅ 删除成功")
                            st.rerun()
                    with col_ca:
                        if st.button("❌ 取消", key=f"cancel_sup_{supplier['id']}"):
                            st.session_state.confirm_delete[f"supplier_{supplier['id']}"] = False
                            st.rerun()

            # 人员信息
            st.markdown("---")
            st.markdown("#### 👥 人员信息")
            contacts = load_supplier_contacts(supplier["id"])

            col_add_c, col_export_c = st.columns([1, 1])
            with col_add_c:
                if st.button("➕ 添加人员", type="primary", use_container_width=True):
                    st.session_state.modal_state["add_contact"] = True
            with col_export_c:
                if contacts:
                    df_contacts = pd.DataFrame(contacts)
                    if st.button("📥 导出", use_container_width=True):
                        export_to_csv(df_contacts, f"contacts_{supplier['name']}.csv")

            if contacts:
                contacts_df = pd.DataFrame(contacts)
                display_cols = ["name", "position", "phone", "wechat", "company", "remark"]
                available = [c for c in display_cols if c in contacts_df.columns]
                contacts_df = contacts_df[available].copy()
                contacts_df.columns = ["姓名", "职务", "电话", "微信", "所属公司", "备注"]

                # 添加操作列
                for idx, contact in enumerate(contacts):
                    st.markdown(f"**{contact.get('name', '')}** | {contact.get('position', '-')} | {contact.get('phone', '-')}")
                    col_e, col_d = st.columns([1, 1])
                    with col_e:
                        if st.button("✏️", key=f"edit_c_{contact['id']}"):
                            st.session_state.modal_state["edit_contact"] = contact["id"]
                    with col_d:
                        if st.button("🗑️", key=f"del_c_{contact['id']}"):
                            st.session_state.confirm_delete[f"contact_{contact['id']}"] = True

                    if st.session_state.confirm_delete.get(f"contact_{contact['id']}"):
                        st.warning(f"⚠️ 确定删除人员「{contact.get('name')}」吗？")
                        col_conf, col_can = st.columns(2)
                        with col_conf:
                            if st.button("✅ 确认", type="primary", key=f"confirm_c_{contact['id']}"):
                                supabase_delete("supplier_contacts", {"id=eq." + contact["id"]})
                                st.session_state.confirm_delete[f"contact_{contact['id']}"] = False
                                st.cache_data.clear()
                                st.rerun()
                        with col_can:
                            if st.button("❌ 取消", key=f"cancel_c_{contact['id']}"):
                                st.session_state.confirm_delete[f"contact_{contact['id']}"] = False
                                st.rerun()

                    st.divider()
            else:
                st.info("暂无人员信息")

            # 物料信息
            st.markdown("---")
            st.markdown("#### 📦 相关物料")
            materials = load_supplier_materials(supplier["id"])

            col_add_m, col_export_m = st.columns([1, 1])
            with col_add_m:
                if st.button("➕ 添加物料", type="primary", use_container_width=True):
                    st.session_state.modal_state["add_material"] = True
            with col_export_m:
                if materials:
                    df_materials = pd.DataFrame(materials)
                    if st.button("📥 导出", use_container_width=True):
                        export_to_csv(df_materials, f"materials_{supplier['name']}.csv")

            if materials:
                for material in materials:
                    price_excl = material.get("price_excl_tax", 0)
                    price_incl = material.get("price_incl_tax", 0)
                    tax_rate = material.get("tax_rate", 0)
                    st.markdown(f"**{material.get('name', '')}** | {material.get('spec', '-')} | "
                               f"¥{float(price_excl):.2f} (税{float(tax_rate)*100:.0f}%) | ¥{float(price_incl):.2f}")

                    col_e, col_d = st.columns([1, 1])
                    with col_e:
                        if st.button("✏️", key=f"edit_m_{material['id']}"):
                            st.session_state.modal_state["edit_material"] = material["id"]
                    with col_d:
                        if st.button("🗑️", key=f"del_m_{material['id']}"):
                            st.session_state.confirm_delete[f"material_{material['id']}"] = True

                    if st.session_state.confirm_delete.get(f"material_{material['id']}"):
                        st.warning(f"⚠️ 确定删除物料「{material.get('name')}」吗？")
                        col_conf, col_can = st.columns(2)
                        with col_conf:
                            if st.button("✅ 确认", type="primary", key=f"confirm_m_{material['id']}"):
                                supabase_delete("supplier_materials", {"id=eq." + material["id"]})
                                st.session_state.confirm_delete[f"material_{material['id']}"] = False
                                st.cache_data.clear()
                                st.rerun()
                        with col_can:
                            if st.button("❌ 取消", key=f"cancel_m_{material['id']}"):
                                st.session_state.confirm_delete[f"material_{material['id']}"] = False
                                st.rerun()

                    st.divider()
            else:
                st.info("暂无物料信息")

    # 渲染各种弹窗
    render_supplier_modal(suppliers)
    render_contact_modal()
    render_material_modal()

def render_supplier_modal(existing_suppliers):
    """供应商新增/编辑弹窗"""
    modal_key = "add_supplier"
    edit_key = st.session_state.modal_state.get("edit_supplier")

    if st.session_state.get(modal_key) or edit_key:
        with st.container():
            st.markdown("""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
                background-color: #f8f0ff;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #d8b8ff;
            }
            </style>
            """, unsafe_allow_html=True)

        is_edit = edit_key is not None
        edit_data = None
        if is_edit:
            edit_data = next((s for s in existing_suppliers if s.get("id") == edit_key), None)
            st.markdown("### ✏️ 编辑供应商")
        else:
            st.markdown("### ➕ 新增供应商")

        with st.form(f"supplier_form_{modal_key}", clear_on_submit=not is_edit):
            st.markdown("**📋 基本信息**")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("单位名称 *", placeholder="必填",
                                    value=edit_data.get("name", "") if edit_data else "")
            with c2:
                phone = st.text_input("电话",
                                     value=edit_data.get("phone", "") if edit_data else "")

            c3, c4 = st.columns(2)
            with c3:
                address = st.text_input("地址",
                                       value=edit_data.get("address", "") if edit_data else "")
            with c4:
                legal_person = st.text_input("法人",
                                            value=edit_data.get("legal_person", "") if edit_data else "")

            c5, c6 = st.columns(2)
            with c5:
                credit_code = st.text_input("统一社会信用代码",
                                           value=edit_data.get("credit_code", "") if edit_data else "")
            with c6:
                business_desc = st.text_input("相关业务",
                                              value=edit_data.get("business_desc", "") if edit_data else "")

            st.markdown("**🏦 银行信息**")
            c7, c8 = st.columns(2)
            with c7:
                bank_name = st.text_input("开户银行",
                                         value=edit_data.get("bank_name", "") if edit_data else "")
            with c8:
                bank_account = st.text_input("银行账号",
                                             value=edit_data.get("bank_account", "") if edit_data else "")

            col_save, col_close = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)
            with col_close:
                closed = st.form_submit_button("关闭", use_container_width=True)

            if closed:
                st.session_state.modal_state[modal_key] = False
                if "edit_supplier" in st.session_state.modal_state:
                    del st.session_state.modal_state["edit_supplier"]
                st.rerun()

            if submitted:
                if not name:
                    st.error("❌ 单位名称不能为空")
                else:
                    data = {
                        "name": name,
                        "phone": phone or "",
                        "address": address or "",
                        "legal_person": legal_person or "",
                        "credit_code": credit_code or "",
                        "business_desc": business_desc or "",
                        "bank_name": bank_name or "",
                        "bank_account": bank_account or ""
                    }

                    if is_edit and edit_data:
                        if supabase_update("suppliers", data, {"id=eq." + edit_key}):
                            st.success("✅ 供应商更新成功！")
                            st.session_state["selected_supplier"] = name
                        else:
                            st.error("❌ 更新失败")
                    else:
                        data["id"] = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
                        if supabase_insert("suppliers", data):
                            st.success("✅ 供应商添加成功！")
                            st.session_state["selected_supplier"] = name
                        else:
                            st.error("❌ 添加失败")

                    st.session_state.modal_state[modal_key] = False
                    if "edit_supplier" in st.session_state.modal_state:
                        del st.session_state.modal_state["edit_supplier"]
                    st.cache_data.clear()
                    st.rerun()

def render_contact_modal():
    """联系人新增/编辑弹窗"""
    modal_key = "add_contact"
    edit_key = st.session_state.modal_state.get("edit_contact")
    suppliers = load_suppliers()
    contacts = load_supplier_contacts() if suppliers else []

    if st.session_state.get(modal_key) or edit_key:
        st.markdown("### ➕ 添加人员" if not edit_key else "### ✏️ 编辑人员")

        edit_data = None
        if edit_key:
            edit_data = next((c for c in contacts if c.get("id") == edit_key), None)

        selected_supplier_name = st.session_state.get("selected_supplier", "")

        with st.form(f"contact_form_{modal_key}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                c_name = st.text_input("姓名 *", placeholder="必填",
                                      value=edit_data.get("name", "") if edit_data else "")
            with c2:
                c_position = st.text_input("职务",
                                          value=edit_data.get("position", "") if edit_data else "")

            c3, c4 = st.columns(2)
            with c3:
                c_phone = st.text_input("联系电话",
                                        value=edit_data.get("phone", "") if edit_data else "")
            with c4:
                c_wechat = st.text_input("微信",
                                        value=edit_data.get("wechat", "") if edit_data else "")

            c_company = st.text_input("所属公司",
                                     value=edit_data.get("company", "") if edit_data else selected_supplier_name)
            c_remark = st.text_input("备注",
                                    value=edit_data.get("remark", "") if edit_data else "")

            col_save, col_close = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)
            with col_close:
                closed = st.form_submit_button("关闭", use_container_width=True)

            if closed:
                st.session_state.modal_state[modal_key] = False
                if "edit_contact" in st.session_state.modal_state:
                    del st.session_state.modal_state["edit_contact"]
                st.rerun()

            if submitted:
                if not c_name:
                    st.error("❌ 姓名不能为空")
                else:
                    # 找到供应商ID
                    supplier_id = None
                    for s in suppliers:
                        if s.get("name") == (c_company or selected_supplier_name):
                            supplier_id = s.get("id")
                            break

                    if not supplier_id and suppliers:
                        supplier_id = suppliers[0].get("id")

                    if supplier_id:
                        data = {
                            "name": c_name,
                            "position": c_position or "",
                            "phone": c_phone or "",
                            "wechat": c_wechat or "",
                            "company": c_company or selected_supplier_name,
                            "remark": c_remark or ""
                        }

                        if edit_key and edit_data:
                            if supabase_update("supplier_contacts", data, {"id=eq." + edit_key}):
                                st.success("✅ 人员更新成功！")
                            else:
                                st.error("❌ 更新失败")
                        else:
                            data["id"] = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
                            data["supplier_id"] = supplier_id
                            if supabase_insert("supplier_contacts", data):
                                st.success("✅ 人员添加成功！")
                            else:
                                st.error("❌ 添加失败")

                        st.session_state.modal_state[modal_key] = False
                        if "edit_contact" in st.session_state.modal_state:
                            del st.session_state.modal_state["edit_contact"]
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 未找到供应商")

def render_material_modal():
    """物料新增/编辑弹窗"""
    modal_key = "add_material"
    edit_key = st.session_state.modal_state.get("edit_material")
    suppliers = load_suppliers()
    materials = load_supplier_materials() if suppliers else []

    if st.session_state.get(modal_key) or edit_key:
        st.markdown("### ➕ 添加物料" if not edit_key else "### ✏️ 编辑物料")

        edit_data = None
        if edit_key:
            edit_data = next((m for m in materials if m.get("id") == edit_key), None)

        with st.form(f"material_form_{modal_key}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                m_name = st.text_input("物料名称 *", placeholder="必填",
                                      value=edit_data.get("name", "") if edit_data else "")
            with c2:
                m_spec = st.text_input("规格",
                                       value=edit_data.get("spec", "") if edit_data else "")

            c3, c4 = st.columns(2)
            with c3:
                m_unit = st.text_input("单位",
                                      value=edit_data.get("unit", "") if edit_data else "")
            with c4:
                price_excl_default = float(edit_data.get("price_excl_tax", 0)) if edit_data else 0.0
                m_price_excl = st.number_input("不含税单价 (元)", min_value=0.0, step=0.01, format="%.2f",
                                               value=price_excl_default)

            c5, c6 = st.columns(2)
            with c5:
                tax_options = {"13%": 0.13, "9%": 0.09, "6%": 0.06, "3%": 0.03, "0%": 0.0}
                tax_default = 0.13
                if edit_data:
                    tax_rate = float(edit_data.get("tax_rate", 0))
                    for label, rate in tax_options.items():
                        if abs(rate - tax_rate) < 0.001:
                            tax_default = rate
                            break
                tax_label = st.selectbox("税率", options=list(tax_options.keys()),
                                         index=list(tax_options.values()).index(tax_default))
                m_tax_rate = tax_options[tax_label]
            with c6:
                price_incl_default = float(edit_data.get("price_incl_tax", m_price_excl * (1 + m_tax_rate))) if edit_data else 0.0
                m_incl_tax = st.number_input("含税单价 (元)", min_value=0.0, step=0.01, format="%.2f",
                                             value=price_incl_default)

            m_freight = st.selectbox("是否含运",
                                   options=["否", "是"],
                                   index=1 if edit_data and edit_data.get("includes_freight") == "是" else 0)
            m_remark = st.text_input("备注",
                                    value=edit_data.get("remark", "") if edit_data else "")

            col_save, col_close = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)
            with col_close:
                closed = st.form_submit_button("关闭", use_container_width=True)

            if closed:
                st.session_state.modal_state[modal_key] = False
                if "edit_material" in st.session_state.modal_state:
                    del st.session_state.modal_state["edit_material"]
                st.rerun()

            if submitted:
                if not m_name:
                    st.error("❌ 物料名称不能为空")
                else:
                    # 找到供应商ID
                    supplier_id = None
                    selected_supplier = st.session_state.get("selected_supplier", "")
                    for s in suppliers:
                        if s.get("name") == selected_supplier:
                            supplier_id = s.get("id")
                            break

                    if not supplier_id and suppliers:
                        supplier_id = suppliers[0].get("id")

                    if supplier_id:
                        data = {
                            "name": m_name,
                            "spec": m_spec or "",
                            "unit": m_unit or "",
                            "price_excl_tax": float(m_price_excl),
                            "tax_rate": float(m_tax_rate),
                            "price_incl_tax": float(m_incl_tax),
                            "includes_freight": m_freight,
                            "remark": m_remark or ""
                        }

                        if edit_key and edit_data:
                            if supabase_update("supplier_materials", data, {"id=eq." + edit_key}):
                                st.success("✅ 物料更新成功！")
                            else:
                                st.error("❌ 更新失败")
                        else:
                            data["id"] = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
                            data["supplier_id"] = supplier_id
                            if supabase_insert("supplier_materials", data):
                                st.success("✅ 物料添加成功！")
                            else:
                                st.error("❌ 添加失败")

                        st.session_state.modal_state[modal_key] = False
                        if "edit_material" in st.session_state.modal_state:
                            del st.session_state.modal_state["edit_material"]
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 未找到供应商")


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
