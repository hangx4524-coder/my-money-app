import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

# 设置网页标题和图标
st.set_page_config(page_title="私人财富管家", page_icon="💰", layout="wide")

DATA_FILE = "my_ledger.csv"

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["日期", "类型", "分类", "金额", "备注"]).to_csv(DATA_FILE, index=False)

st.title("💰 我的私人财富管家")

tab1, tab2 = st.tabs(["✍️ 记账日常", "📊 财富报表"])

# ----------------- 标签页 1：记账 -----------------
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("记一笔")
        record_type = st.radio("这笔钱是：", ["支出", "收入"], horizontal=True)
        categories = {
            "支出": ["餐饮", "交通", "购物", "居住", "娱乐", "医疗", "其他"],
            "收入": ["工资", "理财", "兼职", "其他"]
        }
        
        with st.form("记账表单", clear_on_submit=True):
            record_date = st.date_input("日期", datetime.date.today())
            category = st.selectbox("分类", categories[record_type])
            amount = st.number_input("金额 (元)", min_value=0.01, step=10.0, format="%.2f")
            note = st.text_input("备注", placeholder="例如：和朋友去吃火锅...")
            submitted = st.form_submit_button("💾 保存")
            
            if submitted:
                df = pd.read_csv(DATA_FILE)
                new_record = pd.DataFrame([{"日期": record_date, "类型": record_type, "分类": category, "金额": amount, "备注": note}])
                df = pd.concat([df, new_record], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success(f"✅ 成功记录：{record_date} ｜ {record_type} ｜ {amount}元")

    with col2:
        st.subheader("📜 最近账单")
        df_display = pd.read_csv(DATA_FILE)
        if not df_display.empty:
            st.dataframe(df_display.sort_values(by="日期", ascending=False).head(5), use_container_width=True, hide_index=True)
        else:
            st.info("还没有账单哦，赶紧去记你的第一笔账吧！")


# ----------------- 标签页 2：数据报表与智能建议 -----------------
with tab2:
    st.subheader("📈 财务数据可视化与分析")
    df = pd.read_csv(DATA_FILE)
    
    if df.empty:
        st.warning("暂无数据，请先去「记账日常」记几笔账再来看图表哦！")
    else:
        df['日期'] = pd.to_datetime(df['日期'])
        df['年月'] = df['日期'].dt.strftime("%Y-%m")
        
        months = df['年月'].unique()
        selected_month = st.selectbox("📅 选择月份查看", sorted(months, reverse=True))
        
        month_data = df[df['年月'] == selected_month]
        
        if month_data.empty:
            st.info("这个月你还没有记账记录。")
        else:
            total_expense = month_data[month_data['类型'] == '支出']['金额'].sum()
            total_income = month_data[month_data['类型'] == '收入']['金额'].sum()
            balance = total_income - total_expense
            
            # --- 1. 核心指标区 ---
            col1, col2, col3 = st.columns(3)
            col1.metric(label="本月总支出", value=f"¥ {total_expense:.2f}")
            col2.metric(label="本月总收入", value=f"¥ {total_income:.2f}")
            col3.metric(label="本月结余", value=f"¥ {balance:.2f}")
            
            st.divider()

            # --- 2. 📈 每日收支趋势折线图（✨ 完美优化版） ---
            st.write("**🗓️ 本月每日收支趋势**")
            trend_data = month_data.groupby(['日期', '类型'])['金额'].sum().reset_index()
            trend_data = trend_data.sort_values(by='日期')
            
            if not trend_data.empty:
                # 【改动1】：加入了 text='金额'，让数字绑定在点上
                fig_line = px.line(trend_data, x='日期', y='金额', color='类型', markers=True, text='金额',
                                   color_discrete_map={"支出": "#FF6B6B", "收入": "#4ECDC4"}) 
                
                # 【改动2】：调整数字显示的位置（显示在点正上方），并且只保留两位小数
                fig_line.update_traces(textposition="top center", texttemplate="%{text:.2f}")
                
                # 【改动3】：强制 X 轴只显示“月-日”，并且严格按照1天的间隔划分（不再出现时分秒）
                fig_line.update_xaxes(
                    tickformat="%m-%d",    # 只显示月份和日期，例如 04-21
                    dtick="86400000"       # 魔法数字：86400000 毫秒刚好是 1 天的时间
                )
                
                fig_line.update_layout(xaxis_title="", yaxis_title="金额 (元)") 
                st.plotly_chart(fig_line, use_container_width=True)
            
            st.divider()
            
            # --- 3. 饼图区 ---
            sub_tab_exp, sub_tab_inc = st.tabs(["💸 支出构成", "💰 收入构成"])
            
            with sub_tab_exp:
                expense_data = month_data[month_data['类型'] == '支出']
                if not expense_data.empty:
                    expense_pie = expense_data.groupby('分类')['金额'].sum().reset_index()
                    fig_exp = px.pie(expense_pie, values='金额', names='分类', hole=0.4, 
                                     color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_exp, use_container_width=True)
            
            with sub_tab_inc:
                income_data = month_data[month_data['类型'] == '收入']
                if not income_data.empty:
                    income_pie = income_data.groupby('分类')['金额'].sum().reset_index()
                    fig_inc = px.pie(income_pie, values='金额', names='分类', hole=0.4,
                                     color_discrete_sequence=px.colors.qualitative.Set2)
                    st.plotly_chart(fig_inc, use_container_width=True)

            st.divider()

            # --- 4. 🤖 丢丢的智能理财建议 ---
            st.subheader("🤖 丢丢的本月财富诊断书")
            
            if total_income == 0:
                st.error("🚨 **红色预警**：本月暂时没有收入进账！目前的策略必须是“极致开源节流”。建议盘点一下手头的存款还能支撑几个月，并尽快寻找收入来源。")
            else:
                saving_rate = (balance / total_income) * 100
                
                if not expense_data.empty:
                    top_expense_category = expense_pie.sort_values(by='金额', ascending=False).iloc[0]['分类']
                    top_expense_amount = expense_pie.sort_values(by='金额', ascending=False).iloc[0]['金额']
                    top_expense_ratio = (top_expense_amount / total_expense) * 100
                else:
                    top_expense_category = "无"
                    top_expense_ratio = 0
                
                if balance < 0:
                    st.warning(f"⚠️ **赤字警告**：本月你已经超支了 **{abs(balance):.2f}** 元！\n\n"
                               f"🔍 **丢丢侦探发现**：你的最大开销是「**{top_expense_category}**」，占了总支出的 **{top_expense_ratio:.1f}%**。下个月一定要重点控制这一项的冲动消费，不要让财务漏洞越来越大哦！")
                
                elif 0 <= saving_rate < 20:
                    st.info(f"💡 **初级段位**：本月有结余，但储蓄率仅为 **{saving_rate:.1f}%**，属于“月光边缘”。\n\n"
                            f"📈 **丢丢建议**：理财的第一步是强制储蓄。建议你下个月发工资时，先强制把 20% 存起来，剩下的 80% 再用来消费。另外，本月「**{top_expense_category}**」花费较多，可以看看有没有压缩空间。")
                    
                elif 20 <= saving_rate < 50:
                    st.success(f"🌟 **理财达人**：太棒了！本月储蓄率达到 **{saving_rate:.1f}%**，你的财务非常健康！\n\n"
                               f"🚀 **丢丢建议**：你已经养成了良好的消费习惯。建议将这笔结余分成三份：日常备用金、稳健理财（如固收+）和进阶投资（如定投指数基金），让钱生钱！")
                    
                else:
                    st.balloons()
                    st.success(f"👑 **财富大师**：膜拜！本月储蓄率高达 **{saving_rate:.1f}%**，你简直是攒钱小天才！\n\n"
                               f"🏰 **丢丢建议**：凭借这么高的储蓄率，你实现“FIRE（财务自由，提前退休）”的目标会比普通人快很多！继续保持，稳健投资，时间会给你最好的复利回报！")