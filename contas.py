import streamlit as st
import pandas as pd
import datetime
import os
import base64
import io
import calendar
import plotly.graph_objects as go
from fpdf import FPDF

# Inicialização do session_state para edição inline
if 'modo_edicao' not in st.session_state:
    st.session_state['modo_edicao'] = False
if 'index_edicao' not in st.session_state:
    st.session_state['index_edicao'] = None
if 'df_edicao' not in st.session_state:
    st.session_state['df_edicao'] = 'pendente'  # Pode ser 'pendente' ou 'historico'

# Definir os caminhos dos arquivos CSV
CSV_FILE = "contas_a_pagar.csv"
HISTORICO_FILE = "historico_pagamentos.csv"
SERVICOS_FILE = "servicos_cofap.csv"  # Novo arquivo para serviços da Cofap
# Definir o caminho do arquivo CSV para contas recorrentes
RECORRENTES_FILE = "contas_recorrentes.csv"

# Carregar ou criar o arquivo de contas recorrentes
if os.path.exists(RECORRENTES_FILE):
    recorrentes_df = pd.read_csv(RECORRENTES_FILE, parse_dates=["Próximo Vencimento"])
else:
    recorrentes_df = pd.DataFrame(columns=[
        "Descrição", "Valor", "Próximo Vencimento", "Frequência", 
        "Dia Vencimento", "Última Geração", "Ativa"
    ])
    # Salvar o arquivo vazio
    recorrentes_df.to_csv(RECORRENTES_FILE, index=False)
# Carregar dados dos serviços Cofap
if os.path.exists(SERVICOS_FILE):
    servicos_df = pd.read_csv(SERVICOS_FILE)
    
    # Converter a coluna 'Dia' para datetime
    if 'Dia' in servicos_df.columns:
        servicos_df['Dia'] = pd.to_datetime(servicos_df['Dia'], errors='coerce')
else:
    # Estrutura inicial do DataFrame
    servicos_df = pd.DataFrame(columns=[
        "Funcionario", "Equipamento", "Dia", "Valor diaria", 
        "Pedidos de compra", "Situação"
    ])
    
    # Inserir dados do seu PDF aqui (você também pode fazer isso manualmente pelo app)
    # Exemplo dos primeiros registros:
    dados_iniciais = [
        {"Funcionario": "Richard", "Equipamento": "Empilhadeira", "Dia": "04/01/2024", 
         "Valor diaria": 4000.00, "Pedidos de compra": "", "Situação": 1500.00},
        {"Funcionario": "Richard", "Equipamento": "Empilhadeira", "Dia": "05/01/2024", 
         "Valor diaria": 4000.00, "Pedidos de compra": "", "Situação": -2500.00},
        # ... você pode adicionar mais dados aqui se quiser
    ]
    
    # Criar DataFrame e salvar
    if dados_iniciais:
        temp_df = pd.DataFrame(dados_iniciais)
        servicos_df = pd.concat([servicos_df, temp_df], ignore_index=True)
        servicos_df['Dia'] = pd.to_datetime(servicos_df['Dia'], errors='coerce')
        servicos_df.to_csv(SERVICOS_FILE, index=False)

# Adicione esta função auxiliar no início do arquivo, após as importações

def obter_dia_semana(data, formato='curto'):
    """
    Retorna o dia da semana em português para uma data específica.
    
    Args:
        data: Um objeto datetime.date ou datetime.datetime
        formato: 'curto' para versão abreviada (Dom), 'longo' para versão completa (Domingo)
    
    Returns:
        String com o nome do dia da semana em português
    """
    dias_semana_curtos = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    dias_semana_longos = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 
                         'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    
    # O método weekday() retorna 0 para segunda, 1 para terça, etc.
    # 6 para domingo
    indice = data.weekday()
    
    # Converte para o sistema brasileiro onde domingo é o primeiro dia
    if indice == 6:  # Se for domingo (6 no sistema do Python)
        indice = 6
    else:
        indice = indice
        
    if formato == 'curto':
        return dias_semana_curtos[indice]
    else:
        return dias_semana_longos[indice]


# Agora, você pode usar isso para verificar se o calendário está correto:
# Adicione este código temporariamente no início da função create_calendar_view
# para depuração:

def formatar_real(valor):
    """Formata o valor para o formato de real brasileiro (R$ X.XXX,XX)"""
    if pd.isna(valor):
        return ""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def create_calendar_view(df, year, month):
    # Código de depuração para verificar o dia da semana
    hoje = datetime.date.today()
    dia_semana_hoje = obter_dia_semana(hoje, 'longo')
    st.write(f"Hoje é {hoje.day}/{hoje.month}/{hoje.year}, {dia_semana_hoje}")
    
    # Para uma data específica (16 de março)
    data_16marco = datetime.date(2025, 3, 16)
    dia_semana_16marco = obter_dia_semana(data_16marco, 'longo')
    st.write(f"16/3/2025 é um(a) {dia_semana_16marco}")
    
    # Resto do código do calendário...
    
# Função para exportar dados para CSV
def export_to_csv(df, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV</a>'
    return href

# Função para exportar dados para PDF
def export_to_pdf(df, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Adicionar título
    pdf.cell(200, 10, txt="Relatório de Contas a Pagar", ln=True, align='C')
    pdf.ln(10)
    
    # Adicionar data de geração
    pdf.cell(200, 10, txt=f"Gerado em: {datetime.date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    
    # Cabeçalhos
    col_width = 40
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(col_width, 10, "Descrição", border=1)
    pdf.cell(col_width, 10, "Valor (R$)", border=1)
    pdf.cell(col_width, 10, "Vencimento", border=1)
    pdf.cell(col_width, 10, "Status", border=1)
    pdf.ln()
    
    # Dados
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(col_width, 10, str(row['Descrição']), border=1)
        pdf.cell(col_width, 10, f"{row['Valor']:.2f}", border=1)
        
        # Corrigir o tratamento da data de vencimento
        data_vencimento = row['Data de Vencimento']
        if isinstance(data_vencimento, pd.Timestamp):
            # Se for um objeto Timestamp do pandas, use o método .date()
            data_str = data_vencimento.date().strftime('%d/%m/%Y')
        else:
            # Se for uma string ou outro tipo, tente converter para datetime
            try:
                data_str = pd.to_datetime(data_vencimento).strftime('%d/%m/%Y')
            except:
                data_str = str(data_vencimento)
        
        pdf.cell(col_width, 10, data_str, border=1)
        pdf.cell(col_width, 10, str(row['Status']), border=1)
        pdf.ln()
    
    # Salvar PDF em buffer
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    # Converter para base64
    b64 = base64.b64encode(pdf_buffer.read()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF</a>'
    return href

# Função auxiliar para calcular próxima data
def calcular_proxima_data(data_atual, frequencia, dia_vencimento):
    data_atual = pd.to_datetime(data_atual)
    
    if frequencia == "Mensal":
        proximo_mes = data_atual.month + 1
        proximo_ano = data_atual.year
        
        if proximo_mes > 12:
            proximo_mes = 1
            proximo_ano += 1
    elif frequencia == "Trimestral":
        proximo_mes = data_atual.month + 3
        proximo_ano = data_atual.year
        
        while proximo_mes > 12:
            proximo_mes -= 12
            proximo_ano += 1
    elif frequencia == "Semestral":
        proximo_mes = data_atual.month + 6
        proximo_ano = data_atual.year
        
        while proximo_mes > 12:
            proximo_mes -= 12
            proximo_ano += 1
    else:  # Anual
        proximo_mes = data_atual.month
        proximo_ano = data_atual.year + 1
    
    # Garantir que o dia seja válido
    ultimo_dia = calendar.monthrange(proximo_ano, proximo_mes)[1]
    dia_efetivo = min(dia_vencimento, ultimo_dia)
    
    return datetime.date(proximo_ano, proximo_mes, dia_efetivo)

def create_calendar_view(df, year, month):
    # Filtrar contas recorrentes do mês e ano específicos
    hoje = datetime.date.today()
    contas_recorrentes_pendentes = recorrentes_df[
        (recorrentes_df["Ativa"] == True) & 
        (pd.to_datetime(recorrentes_df["Próximo Vencimento"]).dt.month == month) &
        (pd.to_datetime(recorrentes_df["Próximo Vencimento"]).dt.year == year)
    ]

    # Preparar lista de contas recorrentes
    contas_recorrentes = []
    for _, row in contas_recorrentes_pendentes.iterrows():
        conta_recorrente = pd.DataFrame({
            "Descrição": [f"{row['Descrição']} (Recorrente)"],
            "Valor": [row['Valor']],
            "Data de Vencimento": [row['Próximo Vencimento']],
            "Status": ["Pendente"],
            "Origem": ["Recorrente"]
        })
        contas_recorrentes.append(conta_recorrente)

    # Combinar DataFrames
    if not contas_recorrentes_pendentes.empty:
        df = pd.concat([df] + contas_recorrentes, ignore_index=True)
    
    num_days = calendar.monthrange(year, month)[1]
    cal_df = pd.DataFrame({'day': range(1, num_days + 1)})
    
    # Filtrar contas do mês e ano específicos
    month_df = df[
        (df['Data de Vencimento'].dt.month == month) & 
        (df['Data de Vencimento'].dt.year == year)
    ]
    
    # Inicializar figura
    fig = go.Figure()
    
    # Criar um calendário como uma tabela
    # Nome dos meses em português
    meses_pt = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    month_name = meses_pt[month - 1]
    
    # Semana no formato brasileiro (começando no domingo)
    weekdays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    
    # Pré-configurar o calendário para começar no domingo (6)
    calendar.setfirstweekday(6)  # 6 = domingo
    cal = calendar.monthcalendar(year, month)
    
    
    # Preparar dados para o calendário
    cell_values = [weekdays]
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append("")
            else:
                week_data.append(day)
        cell_values.append(week_data)
    
    # Organizar dados por dia
    contas_por_dia = {}
    for _, row in month_df.iterrows():
        day = row['Data de Vencimento'].day
        if day not in contas_por_dia:
            contas_por_dia[day] = []
        contas_por_dia[day].append(row)
    
    # Criar cores para o calendário
    cell_colors = []
    cell_text = []
    
    # Cabeçalho
    cell_colors.append(['#CCCCCC'] * 7)
    cell_text.append(weekdays)
    
    # Calcular cores para células baseadas em contas
    hoje = datetime.date.today()
    
    for week in cal:
        week_colors = []
        week_text = []
        for day in week:
            if day == 0:
                week_colors.append('#FFFFFF')
                week_text.append('')
            else:
                # Verificar se este dia tem contas
                if day in contas_por_dia:
                    # Verificar status das contas
                    status_list = [conta['Status'] for conta in contas_por_dia[day]]
                    origem_list = [conta.get('Origem', 'Manual') for conta in contas_por_dia[day]]
                    
                    if 'Pendente' in status_list:
                        current_date = datetime.date(year, month, day)
                        if current_date < hoje:
                            # Contas vencidas
                            if 'Recorrente' in origem_list:
                                week_colors.append('#FF4500')  # Laranja escuro para contas vencidas recorrentes
                            else:
                                week_colors.append('#FF6B6B')  # Vermelho para vencidas normais
                        else:
                            # Contas a vencer
                            if 'Recorrente' in origem_list:
                                week_colors.append('#FFA500')  # Laranja para contas a vencer recorrentes
                            else:
                                week_colors.append('#FFEB3B')  # Amarelo para contas a vencer normais
                    else:
                        # Todas as contas pagas
                        week_colors.append('#4CAF50')  # Verde para pagas
                        
                    # Adicionar número de contas ao texto
                    num_contas = len(contas_por_dia[day])
                    total_valor = sum(conta['Valor'] for conta in contas_por_dia[day])
                    week_text.append(f"{day}<br>{num_contas} conta(s)<br>R$ {total_valor:.2f}")
                else:
                    week_colors.append('#FFFFFF')  # Branco para dias sem contas
                    week_text.append(str(day))
        cell_colors.append(week_colors)
        cell_text.append(week_text)
    
    # Criar tabela
    fig.add_trace(go.Table(
        header=dict(
            values=[f"{month_name} {year}"] * 7,
            fill_color='#4285F4',
            align='center',
            font=dict(color='white', size=16),
            height=40
        ),
        cells=dict(
            values=cell_values,
            fill_color=cell_colors,
            align='center',
            font=dict(color='black', size=14),
            height=60
        )
    ))
    
    # Ajustar layout
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=500
    )
    
    return fig

# Carregar dados existentes
if os.path.exists(HISTORICO_FILE):
    historico = pd.read_csv(HISTORICO_FILE)

    # Se a coluna "Data de Pagamento" não existir, adiciona automaticamente
    if "Data de Pagamento" not in historico.columns:
        historico["Data de Pagamento"] = pd.NaT
else:
    historico = pd.DataFrame(columns=["Descrição", "Valor", "Data de Vencimento", "Data de Pagamento"])

# Converter "Data de Pagamento" para formato de data
historico["Data de Pagamento"] = pd.to_datetime(historico["Data de Pagamento"], errors="coerce")
# Gerar contas recorrentes automaticamente antes de carregar o DataFrame
hoje = pd.Timestamp(datetime.date.today())

if not recorrentes_df.empty:
    for i, row in recorrentes_df[recorrentes_df["Ativa"]].iterrows():
        proxima_data = row["Próximo Vencimento"]
        
        if pd.notna(proxima_data) and proxima_data.date() <= hoje.date():
            nova_conta = pd.DataFrame({
                "Descrição": [f"{row['Descrição']} ({row['Frequência'].lower()})"],
                "Valor": [row["Valor"]],
                "Data de Vencimento": [proxima_data],
                "Status": ["Pendente"],
                "Data de Pagamento": [pd.NaT],
                "Origem": ["Recorrente"]
            })
            
            # Se o arquivo CSV já existir, carregue e adicione a conta
            if os.path.exists(CSV_FILE):
                df_temp = pd.read_csv(CSV_FILE)
                df_temp = pd.concat([df_temp, nova_conta], ignore_index=True)
                df_temp.to_csv(CSV_FILE, index=False)
            else:
                # Se o arquivo não existir, crie com a nova conta
                nova_conta.to_csv(CSV_FILE, index=False)
            
            # Atualizar a conta recorrente
            recorrentes_df.at[i, "Próximo Vencimento"] = pd.Timestamp(
                calcular_proxima_data(proxima_data, row["Frequência"], row["Dia Vencimento"])
            )
            recorrentes_df.at[i, "Última Geração"] = pd.Timestamp(proxima_data)
    
    # Salvar atualizações nas contas recorrentes
    recorrentes_df.to_csv(RECORRENTES_FILE, index=False)


# Carregar ou criar o arquivo de contas a pagar
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE, parse_dates=["Data de Vencimento"])

    # Garantir que a coluna "Status" existe
    if "Status" not in df.columns:
        df["Status"] = "Pendente"
    
    # Garantir que a coluna "Data de Pagamento" existe no df principal
    if "Data de Pagamento" not in df.columns:
        df["Data de Pagamento"] = pd.NaT
else:
    df = pd.DataFrame(columns=["Descrição", "Valor", "Data de Vencimento", "Status", "Data de Pagamento"])
    
# Converter datas para formato de data para evitar erro
df["Data de Vencimento"] = pd.to_datetime(df["Data de Vencimento"], errors="coerce")
df["Data de Pagamento"] = pd.to_datetime(df["Data de Pagamento"], errors="coerce")

# Interface do Dashboard
st.title("💰 Dashboard de Contas a Pagar")

# Modificar a criação de abas para incluir a nova aba de contas recorrentes
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📆 Calendário", "📋 Contas", "🔄 Contas Recorrentes", "🏭 Serviços Cofap"])

# Substitua o trecho de código no tab1 (Dashboard) pelo seguinte:

with tab1:
    # Resumo Financeiro
    st.subheader("📊 Resumo Financeiro")
    hoje = pd.Timestamp(datetime.date.today())
    inicio_mes = hoje.replace(day=1)
    fim_mes = inicio_mes + pd.DateOffset(months=1) - pd.DateOffset(days=1)
    fim_semana = hoje + pd.DateOffset(days=7)
    
    # No bloco de cálculo de valores
    # No bloco de cálculo de valores
    contas_pendentes = df[df["Status"] == "Pendente"]
    valor_total = contas_pendentes["Valor"].sum()
    valor_mes = df[(df["Data de Vencimento"] <= fim_mes) & (df["Status"] == "Pendente")]["Valor"].sum()
    valor_semana = df[(df["Data de Vencimento"] <= fim_semana) & (df["Status"] == "Pendente")]["Valor"].sum()

    # Adicionar valores das contas recorrentes APENAS para mês e semana (não para dívida total)
    if not recorrentes_df.empty:
        for _, conta in recorrentes_df[recorrentes_df["Ativa"]].iterrows():
            proxima_data = conta["Próximo Vencimento"]
            
            # Verificar se a próxima data já chegou ou está no período considerado
            if pd.notna(proxima_data):
                # Se a conta estiver para vencer
                # Verificar se essa conta recorrente já não foi gerada
                conta_desc = f"{conta['Descrição']} ({conta['Frequência'].lower()})"
                ja_gerada = any(
                    (df["Descrição"] == conta_desc) & 
                    (df["Data de Vencimento"] == proxima_data) & 
                    (df["Status"] == "Pendente")
                )
                
                # Se não foi gerada ainda, adicionar APENAS aos valores do mês e semana
                if not ja_gerada:
                    if proxima_data <= fim_mes:
                        valor_mes += conta["Valor"]
                    
                    if proxima_data <= fim_semana:
                        valor_semana += conta["Valor"]
    
    # Adicionar valores das contas recorrentes que ainda não foram geradas
    if not recorrentes_df.empty:
        for _, conta in recorrentes_df[recorrentes_df["Ativa"]].iterrows():
            proxima_data = conta["Próximo Vencimento"]
            
            # Verificar se a próxima data já chegou ou está no período considerado
            if pd.notna(proxima_data):
                # Se a conta estiver para vencer (ainda não foi gerada)
                if proxima_data <= hoje:
                    # Verificar se essa conta recorrente já não foi gerada
                    # (verificamos se existe uma conta com mesma descrição e data de vencimento)
                    conta_desc = f"{conta['Descrição']} ({conta['Frequência'].lower()})"
                    ja_gerada = any(
                        (df["Descrição"] == conta_desc) & 
                        (df["Data de Vencimento"] == proxima_data) & 
                        (df["Status"] == "Pendente")
                    )
                    
                    # Se não foi gerada ainda, adicionar ao valor total
                    if not ja_gerada:
                        valor_total += conta["Valor"]
                        
                        # Verificar se também deve ser adicionada aos valores do mês e semana
                        if proxima_data <= fim_mes:
                            valor_mes += conta["Valor"]
                        
                        if proxima_data <= fim_semana:
                            valor_semana += conta["Valor"]

    # Layout em colunas para o resumo financeiro
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💵 Dívida Total", f"R$ {valor_total:,.2f}")

    with col2:
        st.metric("📅 A pagar este mês", f"R$ {valor_mes:,.2f}")

    with col3:
        st.metric("⏳ A pagar esta semana", f"R$ {valor_semana:,.2f}")

    # O restante do código da tab1 permanece igual
    # Seção de Adicionar Nova Conta
    st.subheader("➕ Adicionar Nova Conta")

    with st.form("nova_conta"):
        descricao = st.text_input("📝 Descrição da Conta")
        valor = st.number_input("💰 Valor da Conta (R$)", min_value=0.0, format="%.2f")
        data_vencimento = st.date_input("📅 Data de Vencimento")

        submitted = st.form_submit_button("Adicionar Conta")

        if submitted:
            nova_conta = pd.DataFrame({
                "Descrição": [descricao],
                "Valor": [valor],
                "Data de Vencimento": [pd.Timestamp(data_vencimento)],
                "Status": ["Pendente"],
                "Data de Pagamento": [pd.NaT]
            })
            df = pd.concat([df, nova_conta], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.success("✅ Conta adicionada com sucesso!")

with tab2:
    # Calendário Visual de Vencimentos
    st.subheader("📆 Calendário de Vencimentos")
    
    # Seleção de mês e ano para o calendário
    col1, col2 = st.columns(2)
    with col1:
        meses_nomes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        mes_index = datetime.date.today().month - 1
        mes_nome = st.selectbox("Mês", meses_nomes, index=mes_index)
        mes_calendario = meses_nomes.index(mes_nome) + 1
    with col2:
        ano_calendario = st.selectbox("Ano", range(2023, 2031), index=2)
    
    # Criar e exibir o calendário
    if not df.empty:
        calendario = create_calendar_view(df, ano_calendario, mes_calendario)
        st.plotly_chart(calendario, use_container_width=True)
        
        # Legenda do calendário
        st.markdown("""
        **Legenda:**
        - 🟨 Amarelo: Contas a vencer
        - 🟥 Vermelho: Contas vencidas
        - 🟩 Verde: Contas pagas
        - ⬜ Branco: Sem contas
        """)
    else:
        st.info("Não há contas cadastradas para exibir no calendário.")

with tab3:
    # Histórico de Contas a Pagar
    st.subheader("📌 Histórico de Contas")
    
    hoje = pd.Timestamp(datetime.date.today())
    contas_vencer = df[(df["Data de Vencimento"] >= hoje) & (df["Status"] == "Pendente")]
    contas_vencidas = df[(df["Data de Vencimento"] < hoje) & (df["Status"] == "Pendente")]
    contas_pagas = historico  # Exibe o histórico de contas pagas
    
    # Confirmação de exclusão
    if 'excluir_conta' in st.session_state and st.session_state['excluir_conta']:
        i = st.session_state['excluir_indice']
        tipo = st.session_state['excluir_tipo']
        descricao = st.session_state['excluir_descricao']
        
        st.warning(f"⚠️ Tem certeza que deseja excluir a conta '{descricao}'?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sim, excluir", key="confirmar_exclusao"):
                if tipo == 'pendente':
                    # Remover a conta do dataframe principal
                    df = df.drop(i)
                    df.to_csv(CSV_FILE, index=False)
                    st.success(f"Conta '{descricao}' excluída com sucesso!")
                else:  # historico
                    # Remover a conta do histórico
                    historico = historico.drop(i)
                    historico.to_csv(HISTORICO_FILE, index=False)
                    st.success(f"Conta '{descricao}' excluída do histórico com sucesso!")
                
                # Limpar dados de exclusão
                for key in ['excluir_conta', 'excluir_indice', 'excluir_tipo', 'excluir_descricao']:
                    if key in st.session_state:
                        del st.session_state[key]
                        
                st.rerun()
        
        with col2:
            if st.button("❌ Não, cancelar", key="cancelar_exclusao"):
                # Limpar dados de exclusão
                for key in ['excluir_conta', 'excluir_indice', 'excluir_tipo', 'excluir_descricao']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    # Exibir o botão de filtro
    aba_opcao = st.radio("Filtrar por", ["📅 Contas a Vencer", "❌ Contas Vencidas", "✅ Contas Pagas"], horizontal=True, key="filtro_contas")
    
    # Verificar se estamos no modo de edição
    if st.session_state['modo_edicao']:
        idx = st.session_state['index_edicao']
        
        if st.session_state['df_edicao'] == 'pendente':
            # Editar conta pendente
            conta_atual = df.loc[idx]
            
            st.subheader(f"✏️ Editando: {conta_atual['Descrição']}")
            
            with st.form("editar_conta_inline"):
                # Campos para editar
                nova_descricao = st.text_input("📝 Nova Descrição", value=conta_atual["Descrição"])
                novo_valor = st.number_input("💰 Novo Valor (R$)", value=float(conta_atual["Valor"]), format="%.2f")
                
                # Para a data, use o valor atual formatado corretamente
                data_atual = conta_atual["Data de Vencimento"]
                if isinstance(data_atual, pd.Timestamp):
                    data_atual = data_atual.date()
                else:
                    # Se não for um timestamp, tente converter
                    try:
                        data_atual = pd.to_datetime(data_atual).date()
                    except:
                        data_atual = datetime.date.today()
                
                nova_data = st.date_input("📅 Nova Data de Vencimento", value=data_atual)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                with col2:
                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                
                if submitted:
                    # Atualizar os valores diretamente pelo índice
                    df.at[idx, "Descrição"] = nova_descricao
                    df.at[idx, "Valor"] = novo_valor
                    df.at[idx, "Data de Vencimento"] = pd.Timestamp(nova_data)
                    
                    # Salvar as alterações
                    df.to_csv(CSV_FILE, index=False)
                    st.success(f"✅ Conta atualizada com sucesso!")
                    
                    # Sair do modo de edição
                    st.session_state['modo_edicao'] = False
                    st.session_state['index_edicao'] = None
                    st.session_state['df_edicao'] = 'pendente'
                    
                    # Recarregar a página
                    st.rerun()
                
                if cancelar:
                    # Sair do modo de edição sem salvar
                    st.session_state['modo_edicao'] = False
                    st.session_state['index_edicao'] = None
                    st.rerun()
        
        else:  # Editar conta do histórico
            # Editar conta do histórico
            conta_atual = historico.loc[idx]
            
            st.subheader(f"✏️ Editando conta paga: {conta_atual['Descrição']}")
            
            with st.form("editar_conta_historico_inline"):
                # Campos para editar
                nova_descricao = st.text_input("📝 Nova Descrição", value=conta_atual["Descrição"])
                novo_valor = st.number_input("💰 Novo Valor (R$)", value=float(conta_atual["Valor"]), format="%.2f")
                
                # Para a data de vencimento
                data_venc_atual = conta_atual["Data de Vencimento"]
                if isinstance(data_venc_atual, pd.Timestamp):
                    data_venc_atual = data_venc_atual.date()
                else:
                    try:
                        data_venc_atual = pd.to_datetime(data_venc_atual).date()
                    except:
                        data_venc_atual = datetime.date.today()
                
                nova_data_venc = st.date_input("📅 Nova Data de Vencimento", value=data_venc_atual)
                
                # Para a data de pagamento
                data_pag_atual = conta_atual["Data de Pagamento"]
                if pd.notna(data_pag_atual) and isinstance(data_pag_atual, pd.Timestamp):
                    data_pag_atual = data_pag_atual.date()
                else:
                    data_pag_atual = datetime.date.today()
                
                nova_data_pag = st.date_input("📅 Nova Data de Pagamento", value=data_pag_atual)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                with col2:
                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                
                if submitted:
                    # Atualizar os valores diretamente pelo índice
                    historico.at[idx, "Descrição"] = nova_descricao
                    historico.at[idx, "Valor"] = novo_valor
                    historico.at[idx, "Data de Vencimento"] = pd.Timestamp(nova_data_venc)
                    historico.at[idx, "Data de Pagamento"] = pd.Timestamp(nova_data_pag)
                    
                    # Salvar as alterações
                    historico.to_csv(HISTORICO_FILE, index=False)
                    st.success(f"✅ Conta do histórico atualizada com sucesso!")
                    
                    # Sair do modo de edição
                    st.session_state['modo_edicao'] = False
                    st.session_state['index_edicao'] = None
                    st.session_state['df_edicao'] = 'pendente'
                    
                    # Recarregar a página
                    st.rerun()
                    
                if cancelar:
                    # Sair do modo de edição sem salvar
                    st.session_state['modo_edicao'] = False
                    st.session_state['index_edicao'] = None
                    st.rerun()
    
    else:
        # Mostrar as contas de acordo com a opção selecionada
        if aba_opcao == "📅 Contas a Vencer":
            st.markdown("### 🟡 Contas a Vencer")
            
            # Adicionar contas recorrentes pendentes
            hoje = pd.Timestamp(datetime.date.today())
            contas_recorrentes_pendentes = recorrentes_df[
                (recorrentes_df["Ativa"] == True)
            ]
            
            # Preparar lista de contas recorrentes
            contas_recorrentes_vencer = []
            for _, row in contas_recorrentes_pendentes.iterrows():
                conta_recorrente = pd.DataFrame({
                    "Descrição": [f"{row['Descrição']} 🔄 (Recorrente)"],
                    "Valor": [row['Valor']],
                    "Data de Vencimento": [row['Próximo Vencimento']],
                    "Status": ["Pendente"],
                    "Origem": ["Recorrente"]
                })
                contas_recorrentes_vencer.append(conta_recorrente)

            # Combinar contas normais com contas recorrentes
            if contas_recorrentes_vencer:
                contas_vencer_combinado = pd.concat([contas_vencer] + contas_recorrentes_vencer, ignore_index=True)
                # Ordenar por data de vencimento
                contas_vencer_combinado = contas_vencer_combinado.sort_values('Data de Vencimento')
                contas_vencer = contas_vencer_combinado

            # Verificar se há contas
            if contas_vencer.empty:
                st.info("Nenhuma conta a vencer no momento.")
            else:
                for i, row in contas_vencer.iterrows():
                    origem = row.get('Origem', 'Normal')
                    
                    # Código para mostrar as contas
                    with st.expander(f"{row['Descrição']} - R$ {row['Valor']:.2f} 🟡 (Vence em {row['Data de Vencimento'].strftime('%d/%m/%Y')})"):
                        st.write(f"**Valor:** R$ {row['Valor']:.2f}")
                        st.write(f"**Data de Vencimento:** {row['Data de Vencimento'].strftime('%d/%m/%Y')}")
                        
                        # Adicionar indicação se é recorrente
                        if origem == 'Recorrente':
                            st.write("**Tipo:** 🔄 Conta Recorrente")
                        
                        # Adicionar botões de ação apenas para contas normais
                        if origem != 'Recorrente':  # Não mostrar botões para contas recorrentes
                            col1, col2, col3 = st.columns([1, 1, 1])
                            
                            with col1:
                                if st.button("✅ Pagar", key=f"pagar_{i}", use_container_width=True):
                                    hoje = pd.Timestamp(datetime.date.today())
                                    
                                    # Atualizar o status da conta
                                    df.loc[i, "Status"] = "Paga"
                                    df.loc[i, "Data de Pagamento"] = hoje
                                    
                                    # Criar um DataFrame com a conta paga
                                    conta_paga = df.loc[[i]].copy()
                                    
                                    # Remover a conta paga do arquivo principal
                                    df = df.drop(i)
                                    df.to_csv(CSV_FILE, index=False)
                                    
                                    # Garantir que a coluna existe no histórico
                                    if "Data de Pagamento" not in historico.columns:
                                        historico["Data de Pagamento"] = pd.NaT
                                    
                                    # Salvar no histórico
                                    historico = pd.concat([historico, conta_paga], ignore_index=True)
                                    historico.to_csv(HISTORICO_FILE, index=False)
                                    
                                    st.success(f"Conta '{row['Descrição']}' foi marcada como paga!")
                                    st.rerun()
                            
                            with col2:
                                if st.button("✏️ Editar", key=f"editar_{i}", use_container_width=True):
                                    # Ativar modo de edição
                                    st.session_state['modo_edicao'] = True
                                    st.session_state['index_edicao'] = i
                                    st.session_state['df_edicao'] = 'pendente'
                                    st.rerun()
                            
                            with col3:
                                if st.button("🗑️ Excluir", key=f"excluir_{i}", use_container_width=True):
                                    # Armazenar a conta a ser excluída na session_state
                                    st.session_state['excluir_conta'] = True
                                    st.session_state['excluir_indice'] = i
                                    st.session_state['excluir_tipo'] = 'pendente'
                                    st.session_state['excluir_descricao'] = row['Descrição']
                                    st.rerun()
                        else:
                            # Para contas recorrentes, mostrar uma mensagem informativa
                            st.info("Para gerenciar esta conta recorrente, acesse a aba 'Contas Recorrentes'")

        elif aba_opcao == "❌ Contas Vencidas":
            st.markdown("### 🔴 Contas Vencidas")
            if contas_vencidas.empty:
                st.info("Nenhuma conta vencida no momento.")
            else:
                for i, row in contas_vencidas.iterrows():
                    with st.expander(f"{row['Descrição']} - R$ {row['Valor']:.2f} 🔴 (Venceu em {row['Data de Vencimento'].strftime('%d/%m/%Y')})"):
                        st.write(f"**Valor:** R$ {row['Valor']:.2f}")
                        st.write(f"**Data de Vencimento:** {row['Data de Vencimento'].strftime('%d/%m/%Y')}")
                        
                        # Adicionar botões de ação
                        col1, col2, col3 = st.columns([1, 1, 1])
                        
                        with col1:
                            if st.button("✅ Pagar", key=f"pagar_vencida_{i}", use_container_width=True):
                                hoje = pd.Timestamp(datetime.date.today())
                                
                                # Atualizar o status da conta
                                df.loc[i, "Status"] = "Paga"
                                df.loc[i, "Data de Pagamento"] = hoje
                                
                                # Criar um DataFrame com a conta paga
                                conta_paga = df.loc[[i]].copy()
                                
                                # Remover a conta paga do arquivo principal
                                df = df.drop(i)
                                df.to_csv(CSV_FILE, index=False)
                                
                                # Garantir que a coluna existe no histórico
                                if "Data de Pagamento" not in historico.columns:
                                    historico["Data de Pagamento"] = pd.NaT
                                
                                # Salvar no histórico
                                historico = pd.concat([historico, conta_paga], ignore_index=True)
                                historico.to_csv(HISTORICO_FILE, index=False)
                                
                                st.success(f"Conta vencida '{row['Descrição']}' foi marcada como paga!")
                                st.rerun()
                        
                        with col2:
                            if st.button("✏️ Editar", key=f"editar_vencida_{i}", use_container_width=True):
                                # Ativar modo de edição
                                st.session_state['modo_edicao'] = True
                                st.session_state['index_edicao'] = i
                                st.session_state['df_edicao'] = 'pendente'
                                st.rerun()
                        
                        with col3:
                            if st.button("🗑️ Excluir", key=f"excluir_vencida_{i}", use_container_width=True):
                                # Armazenar a conta a ser excluída na session_state
                                st.session_state['excluir_conta'] = True
                                st.session_state['excluir_indice'] = i
                                st.session_state['excluir_tipo'] = 'pendente'
                                st.session_state['excluir_descricao'] = row['Descrição']
                                st.rerun()

        elif aba_opcao == "✅ Contas Pagas":
            st.markdown("### ✅ Contas Pagas")
            
            if contas_pagas.empty:
                st.info("Nenhuma conta foi paga ainda.")
            else:
                for i, row in contas_pagas.iterrows():
                    # Tratamento da data de pagamento
                    data_pagamento = row["Data de Pagamento"] if pd.notna(row["Data de Pagamento"]) else "Não informado"
                    data_pagamento_str = data_pagamento.strftime('%d/%m/%Y') if isinstance(data_pagamento, pd.Timestamp) else data_pagamento

                    with st.expander(f"{row['Descrição']} - R$ {row['Valor']:.2f} ✅ (Paga em {data_pagamento_str})"):
                        st.write(f"**Valor:** R$ {row['Valor']:.2f}")
                        # Trate a data de vencimento da mesma forma
                        data_venc = row["Data de Vencimento"]
                        data_venc_str = data_venc.strftime('%d/%m/%Y') if isinstance(data_venc, pd.Timestamp) else str(data_venc)
                        st.write(f"**Data de Vencimento:** {data_venc_str}")
                        st.write(f"**Data de Pagamento:** {data_pagamento_str}")
                        
                        # Adicionar botões de ação
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            if st.button("✏️ Editar", key=f"editar_paga_{i}", use_container_width=True):
                                # Ativar modo de edição
                                st.session_state['modo_edicao'] = True
                                st.session_state['index_edicao'] = i
                                st.session_state['df_edicao'] = 'historico'
                                st.rerun()
                        
                        with col2:
                            if st.button("🗑️ Excluir", key=f"excluir_paga_{i}", use_container_width=True):
                                # Armazenar a conta a ser excluída na session_state
                                st.session_state['excluir_conta'] = True
                                st.session_state['excluir_indice'] = i
                                st.session_state['excluir_tipo'] = 'historico'
                                st.session_state['excluir_descricao'] = row['Descrição']
                                st.rerun()

    # Adicione este código no final da aba Contas (tab3)
    st.markdown("---")
    st.subheader("📊 Exportar Contas para PDF")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 Exportar Contas a Vencer", use_container_width=True):
            # Criar PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Adicionar título
            pdf.cell(200, 10, txt="Relatório de Contas a Vencer", ln=True, align='C')
            pdf.ln(10)
            
            # Adicionar data de geração
            pdf.cell(200, 10, txt=f"Gerado em: {datetime.date.today().strftime('%d/%m/%Y')}", ln=True)
            pdf.ln(10)
            
            # Cabeçalhos
            col_width = 190 / 4  # 4 colunas
            pdf.set_font("Arial", 'B', 12)
            headers = ["Descrição", "Valor (R$)", "Vencimento", "Status"]
            for header in headers:
                pdf.cell(col_width, 10, header, border=1)
            pdf.ln()
            
            # Dados - contas a vencer (pendentes e não vencidas)
            pdf.set_font("Arial", size=10)
            hoje = pd.Timestamp(datetime.date.today())
            contas_a_vencer = df[(df["Status"] == "Pendente") & (df["Data de Vencimento"] >= hoje)]
            
            for _, row in contas_a_vencer.iterrows():
                # Descrição
                pdf.cell(col_width, 10, str(row['Descrição']), border=1)
                # Valor
                pdf.cell(col_width, 10, f"R$ {row['Valor']:,.2f}", border=1)
                # Data de vencimento
                if pd.notna(row['Data de Vencimento']):
                    data_str = pd.to_datetime(row['Data de Vencimento']).strftime('%d/%m/%Y')
                else:
                    data_str = ""
                pdf.cell(col_width, 10, data_str, border=1)
                # Status
                pdf.cell(col_width, 10, str(row['Status']), border=1)
                pdf.ln()
            
            # Método 1: Salvar em arquivo temporário e depois ler
            temp_file = "temp_contas_a_vencer.pdf"
            pdf.output(temp_file)
            
            # Ler o arquivo temporário
            with open(temp_file, "rb") as file:
                pdf_data = file.read()
            
            # Remover o arquivo temporário
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Oferecer para download
            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf_data,
                file_name=f"contas_a_vencer_{datetime.date.today().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf"
            )

    with col2:
        if st.button("📄 Exportar Contas Vencidas", use_container_width=True):
            # Criar PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Adicionar título
            pdf.cell(200, 10, txt="Relatório de Contas Vencidas", ln=True, align='C')
            pdf.ln(10)
            
            # Adicionar data de geração
            pdf.cell(200, 10, txt=f"Gerado em: {datetime.date.today().strftime('%d/%m/%Y')}", ln=True)
            pdf.ln(10)
            
            # Cabeçalhos
            col_width = 190 / 4  # 4 colunas
            pdf.set_font("Arial", 'B', 12)
            headers = ["Descrição", "Valor (R$)", "Vencimento", "Status"]
            for header in headers:
                pdf.cell(col_width, 10, header, border=1)
            pdf.ln()
            
            # Dados - contas vencidas
            pdf.set_font("Arial", size=10)
            hoje = pd.Timestamp(datetime.date.today())
            contas_vencidas = df[(df["Status"] == "Pendente") & (df["Data de Vencimento"] < hoje)]
            
            for _, row in contas_vencidas.iterrows():
                # Descrição
                pdf.cell(col_width, 10, str(row['Descrição']), border=1)
                # Valor
                pdf.cell(col_width, 10, f"R$ {row['Valor']:,.2f}", border=1)
                # Data de vencimento
                if pd.notna(row['Data de Vencimento']):
                    data_str = pd.to_datetime(row['Data de Vencimento']).strftime('%d/%m/%Y')
                else:
                    data_str = ""
                pdf.cell(col_width, 10, data_str, border=1)
                # Status
                pdf.cell(col_width, 10, "Vencida", border=1)
                pdf.ln()
            
            # Método 1: Salvar em arquivo temporário e depois ler
            temp_file = "temp_contas_vencidas.pdf"
            pdf.output(temp_file)
            
            # Ler o arquivo temporário
            with open(temp_file, "rb") as file:
                pdf_data = file.read()
            
            # Remover o arquivo temporário
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Oferecer para download
            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf_data,
                file_name=f"contas_vencidas_{datetime.date.today().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf"
            )

    with col3:
        if st.button("📄 Exportar Contas Pagas", use_container_width=True):
            # Criar PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Adicionar título
            pdf.cell(200, 10, txt="Relatório de Contas Pagas", ln=True, align='C')
            pdf.ln(10)
            
            # Adicionar data de geração
            pdf.cell(200, 10, txt=f"Gerado em: {datetime.date.today().strftime('%d/%m/%Y')}", ln=True)
            pdf.ln(10)
            
            # Cabeçalhos
            col_width = 190 / 5  # 5 colunas
            pdf.set_font("Arial", 'B', 12)
            headers = ["Descrição", "Valor (R$)", "Vencimento", "Pagamento", "Status"]
            for header in headers:
                pdf.cell(col_width, 10, header, border=1)
            pdf.ln()
            
            # Dados - contas pagas do histórico
            pdf.set_font("Arial", size=9)  # Reduzido o tamanho para caber melhor
            
            for _, row in historico.iterrows():
                # Descrição
                pdf.cell(col_width, 10, str(row['Descrição']), border=1)
                # Valor
                pdf.cell(col_width, 10, f"R$ {row['Valor']:,.2f}", border=1)
                # Data de vencimento
                if pd.notna(row['Data de Vencimento']):
                    data_venc_str = pd.to_datetime(row['Data de Vencimento']).strftime('%d/%m/%Y')
                else:
                    data_venc_str = ""
                pdf.cell(col_width, 10, data_venc_str, border=1)
                # Data de pagamento
                if pd.notna(row['Data de Pagamento']):
                    data_pag_str = pd.to_datetime(row['Data de Pagamento']).strftime('%d/%m/%Y')
                else:
                    data_pag_str = ""
                pdf.cell(col_width, 10, data_pag_str, border=1)
                # Status
                pdf.cell(col_width, 10, "Paga", border=1)
                pdf.ln()
            
            # Método 1: Salvar em arquivo temporário e depois ler
            temp_file = "temp_contas_pagas.pdf"
            pdf.output(temp_file)
            
            # Ler o arquivo temporário
            with open(temp_file, "rb") as file:
                pdf_data = file.read()
            
            # Remover o arquivo temporário
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Oferecer para download
            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf_data,
                file_name=f"contas_pagas_{datetime.date.today().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf"
            )
with tab4:
    st.subheader("🔄 Contas Recorrentes")
    
    # Seção para adicionar uma nova conta recorrente
    with st.expander("➕ Adicionar Nova Conta Recorrente", expanded=False):
        with st.form("nova_conta_recorrente"):
            descricao = st.text_input("📝 Descrição da Conta")
            valor = st.number_input("💰 Valor (R$)", min_value=0.0, format="%.2f")
            
            col1, col2 = st.columns(2)
            with col1:
                frequencia = st.selectbox(
                    "🔄 Frequência", 
                    options=["Mensal", "Trimestral", "Semestral", "Anual"]
                )
            
            with col2:
                dia_vencimento = st.number_input(
                    "📅 Dia do Vencimento", 
                    min_value=1, 
                    max_value=31,
                    value=10,  # Valor padrão
                    help="Dia do mês em que a conta vence"
                )
            
            # Data do próximo vencimento
            hoje = datetime.date.today()
            mes_prox_venc = hoje.month
            ano_prox_venc = hoje.year
            
            # Se o dia já passou neste mês, o próximo vencimento será no próximo mês
            if hoje.day > dia_vencimento:
                mes_prox_venc += 1
                if mes_prox_venc > 12:
                    mes_prox_venc = 1
                    ano_prox_venc += 1
            
            # Garantir que o dia seja válido para o mês
            ultimo_dia = calendar.monthrange(ano_prox_venc, mes_prox_venc)[1]
            dia_efetivo = min(dia_vencimento, ultimo_dia)
            
            data_prox_venc = datetime.date(ano_prox_venc, mes_prox_venc, dia_efetivo)
            
            st.info(f"Próximo vencimento será em: {data_prox_venc.strftime('%d/%m/%Y')}")
            
            submitted = st.form_submit_button("Adicionar Conta Recorrente")
            
            if submitted:
                # Adicionar a nova conta recorrente
                nova_recorrente = pd.DataFrame({
                    "Descrição": [descricao],
                    "Valor": [valor],
                    "Próximo Vencimento": [pd.Timestamp(data_prox_venc)],
                    "Frequência": [frequencia],
                    "Dia Vencimento": [dia_vencimento],
                    "Última Geração": [pd.NaT],
                    "Ativa": [True]
                })
                
                # Concatenar com o dataframe existente
                recorrentes_df = pd.concat([recorrentes_df, nova_recorrente], ignore_index=True)
                recorrentes_df.to_csv(RECORRENTES_FILE, index=False)
                
                st.success("✅ Conta recorrente adicionada com sucesso!")
                st.rerun()
    
    # Botão para gerar contas recorrentes deste mês
    if not recorrentes_df.empty and any(recorrentes_df["Ativa"]):
        hoje = datetime.date.today()
        
        if st.button("🔄 Gerar Contas Recorrentes Pendentes", type="primary", use_container_width=True):
            contas_geradas = 0
            st.write("Número de contas recorrentes ativas:", len(recorrentes_df[recorrentes_df["Ativa"]]))
            # Para cada conta recorrente ativa
            for i, row in recorrentes_df[recorrentes_df["Ativa"]].iterrows():
                proxima_data = row["Próximo Vencimento"]
                st.write(f"Verificando conta: {row['Descrição']}")
                st.write(f"Próxima data: {proxima_data}")
                st.write(f"Hoje: {hoje}")
                # Verificar se a próxima data já chegou
                if pd.notna(proxima_data) and proxima_data.date() <= hoje:
                    st.write(f"Gerando conta para: {row['Descrição']}")
                    # Na função de gerar contas recorrentes, modifique a criação do DataFrame
                    nova_conta = pd.DataFrame({
                        "Descrição": [f"{row['Descrição']} ({row['Frequência'].lower()})"],
                        "Valor": [row["Valor"]],
                        "Data de Vencimento": [proxima_data],
                        "Status": ["Pendente"],
                        "Data de Pagamento": [pd.NaT],
                        "Origem": ["Recorrente"]  # Novo campo para identificar origem
                    })
                    # Adicionar ao DataFrame de contas
                    df = pd.concat([df, nova_conta], ignore_index=True)
                    
                    contas_geradas += 1
                    st.write(f"Total de contas geradas: {contas_geradas}")
                    # Calcular a próxima data de vencimento com base na frequência

                    ultima_geracao = proxima_data
                    dia_venc = int(row["Dia Vencimento"])
                    
                    if row["Frequência"] == "Mensal":
                        # Avançar um mês
                        proximo_mes = proxima_data.month + 1
                        proximo_ano = proxima_data.year
                        
                        if proximo_mes > 12:
                            proximo_mes = 1
                            proximo_ano += 1
                        
                        # Ajustar para um dia válido no próximo mês
                        ultimo_dia_prox_mes = calendar.monthrange(proximo_ano, proximo_mes)[1]
                        dia_efetivo = min(dia_venc, ultimo_dia_prox_mes)
                        
                        prox_data = datetime.date(proximo_ano, proximo_mes, dia_efetivo)
                        
                    elif row["Frequência"] == "Trimestral":
                        # Avançar três meses
                        proximo_mes = proxima_data.month + 3
                        proximo_ano = proxima_data.year
                        
                        while proximo_mes > 12:
                            proximo_mes -= 12
                            proximo_ano += 1
                        
                        ultimo_dia_prox_mes = calendar.monthrange(proximo_ano, proximo_mes)[1]
                        dia_efetivo = min(dia_venc, ultimo_dia_prox_mes)
                        
                        prox_data = datetime.date(proximo_ano, proximo_mes, dia_efetivo)
                        
                    elif row["Frequência"] == "Semestral":
                        # Avançar seis meses
                        proximo_mes = proxima_data.month + 6
                        proximo_ano = proxima_data.year
                        
                        while proximo_mes > 12:
                            proximo_mes -= 12
                            proximo_ano += 1
                        
                        ultimo_dia_prox_mes = calendar.monthrange(proximo_ano, proximo_mes)[1]
                        dia_efetivo = min(dia_venc, ultimo_dia_prox_mes)
                        
                        prox_data = datetime.date(proximo_ano, proximo_mes, dia_efetivo)
                        
                    else:  # Anual
                        # Avançar um ano
                        proximo_ano = proxima_data.year + 1
                        proximo_mes = proxima_data.month
                        
                        ultimo_dia_prox_mes = calendar.monthrange(proximo_ano, proximo_mes)[1]
                        dia_efetivo = min(dia_venc, ultimo_dia_prox_mes)
                        
                        prox_data = datetime.date(proximo_ano, proximo_mes, dia_efetivo)
                    
                    # Atualizar a conta recorrente
                    recorrentes_df.at[i, "Próximo Vencimento"] = pd.Timestamp(prox_data)
                    recorrentes_df.at[i, "Última Geração"] = pd.Timestamp(ultima_geracao)
            
            # Salvar as alterações
            df.to_csv(CSV_FILE, index=False)
            recorrentes_df.to_csv(RECORRENTES_FILE, index=False)
            
            if contas_geradas > 0:
                st.success(f"✅ {contas_geradas} conta(s) recorrente(s) gerada(s) com sucesso!")
            else:
                st.info("ℹ️ Não há contas recorrentes pendentes para geração.")
            
            st.rerun()
    
    # Exibir tabela de contas recorrentes
    if not recorrentes_df.empty:
        st.subheader("📋 Lista de Contas Recorrentes")
        
        # Preparar os dados para exibição
        # Preparar os dados para exibição
        df_display = recorrentes_df.copy()
        # Tratamento seguro para colunas de data
        df_display["Próximo Vencimento"] = df_display["Próximo Vencimento"].apply(
            lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "Não definida"
        )
        df_display["Última Geração"] = df_display["Última Geração"].apply(
            lambda x: pd.to_datetime(x, errors='coerce').strftime('%d/%m/%Y') if pd.notna(x) else "Nunca gerada"
        )
        df_display["Valor"] = df_display["Valor"].apply(lambda x: f"R$ {x:,.2f}")
        df_display["Status"] = df_display["Ativa"].apply(lambda x: "✅ Ativa" if x else "❌ Inativa")
        # Selecionar e renomear colunas para exibição
        colunas_exibir = {
            "Descrição": "Descrição",
            "Valor": "Valor",
            "Frequência": "Frequência",
            "Dia Vencimento": "Dia do Mês",
            "Próximo Vencimento": "Próximo Vencimento",
            "Status": "Status"
        }
        
        df_exibir = df_display[list(colunas_exibir.keys())].rename(columns=colunas_exibir)
        
        # Exibir a tabela
        st.dataframe(df_exibir, use_container_width=True)
        
        # Gerenciar contas recorrentes
        st.subheader("⚙️ Gerenciar Contas Recorrentes")
        
        for i, row in recorrentes_df.iterrows():
            with st.expander(f"{row['Descrição']} - {formatar_real(row['Valor'])} ({row['Frequência']})", expanded=False):
                status_ativa = "✅ Ativa" if row["Ativa"] else "❌ Inativa"
                proxima_data = pd.to_datetime(row["Próximo Vencimento"]).strftime('%d/%m/%Y') if pd.notna(row["Próximo Vencimento"]) else "Não definida"
                ultima_geracao = pd.to_datetime(row["Última Geração"]).strftime('%d/%m/%Y') if pd.notna(row["Última Geração"]) else "Nunca gerada"
                
                st.write(f"**Status:** {status_ativa}")
                st.write(f"**Valor:** {formatar_real(row['Valor'])}")
                st.write(f"**Frequência:** {row['Frequência']}")
                st.write(f"**Dia do vencimento:** {int(row['Dia Vencimento'])}")
                st.write(f"**Próximo vencimento:** {proxima_data}")
                st.write(f"**Última geração:** {ultima_geracao}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✏️ Editar", key=f"editar_recorrente_{i}", use_container_width=True):
                        st.session_state['editar_recorrente'] = True
                        st.session_state['indice_recorrente'] = i
                        st.rerun()
                
                with col2:
                    if row["Ativa"]:
                        if st.button("❌ Desativar", key=f"desativar_recorrente_{i}", use_container_width=True):
                            recorrentes_df.at[i, "Ativa"] = False
                            recorrentes_df.to_csv(RECORRENTES_FILE, index=False)
                            st.success(f"Conta '{row['Descrição']}' desativada!")
                            st.rerun()
                    else:
                        if st.button("✅ Ativar", key=f"ativar_recorrente_{i}", use_container_width=True):
                            recorrentes_df.at[i, "Ativa"] = True
                            recorrentes_df.to_csv(RECORRENTES_FILE, index=False)
                            st.success(f"Conta '{row['Descrição']}' ativada!")
                            st.rerun()
                
                with col3:
                    if st.button("🗑️ Excluir", key=f"excluir_recorrente_{i}", use_container_width=True):
                        st.session_state['excluir_recorrente'] = True
                        st.session_state['indice_recorrente'] = i
                        st.session_state['descricao_recorrente'] = row['Descrição']
                        st.rerun()
        
        # Confirmação de exclusão
        if 'excluir_recorrente' in st.session_state and st.session_state['excluir_recorrente']:
            i = st.session_state['indice_recorrente']
            descricao = st.session_state['descricao_recorrente']
            
            st.warning(f"⚠️ Tem certeza que deseja excluir a conta recorrente '{descricao}'?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sim, excluir", key="confirmar_exclusao_recorrente"):
                    # Remover a conta recorrente
                    recorrentes_df = recorrentes_df.drop(i).reset_index(drop=True)
                    recorrentes_df.to_csv(RECORRENTES_FILE, index=False)
                    st.success(f"Conta recorrente '{descricao}' excluída com sucesso!")
                    
                    # Limpar dados de exclusão
                    for key in ['excluir_recorrente', 'indice_recorrente', 'descricao_recorrente']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.rerun()
            
            with col2:
                if st.button("❌ Não, cancelar", key="cancelar_exclusao_recorrente"):
                    # Limpar dados de exclusão
                    for key in ['excluir_recorrente', 'indice_recorrente', 'descricao_recorrente']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        
        # Formulário de edição
        if 'editar_recorrente' in st.session_state and st.session_state['editar_recorrente']:
            i = st.session_state['indice_recorrente']
            conta_atual = recorrentes_df.loc[i]
            
            st.subheader(f"✏️ Editando conta recorrente: {conta_atual['Descrição']}")
            
            with st.form("editar_conta_recorrente"):
                nova_descricao = st.text_input("📝 Nova Descrição", value=conta_atual["Descrição"])
                novo_valor = st.number_input("💰 Novo Valor (R$)", value=float(conta_atual["Valor"]), format="%.2f")
                
                col1, col2 = st.columns(2)
                with col1:
                    nova_frequencia = st.selectbox(
                        "🔄 Nova Frequência", 
                        options=["Mensal", "Trimestral", "Semestral", "Anual"],
                        index=["Mensal", "Trimestral", "Semestral", "Anual"].index(conta_atual["Frequência"])
                    )
                
                with col2:
                    novo_dia_vencimento = st.number_input(
                        "📅 Novo Dia do Vencimento", 
                        min_value=1, 
                        max_value=31,
                        value=int(conta_atual["Dia Vencimento"])
                    )
                
                # Opção para ajustar a próxima data de vencimento
                if pd.notna(conta_atual["Próximo Vencimento"]):
                    prox_venc_atual = pd.to_datetime(conta_atual["Próximo Vencimento"]).date()
                else:
                    prox_venc_atual = datetime.date.today()
                
                nova_prox_data = st.date_input("📅 Nova Data do Próximo Vencimento", value=prox_venc_atual)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                with col2:
                    cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
                
                if submitted:
                    # Atualizar os valores
                    recorrentes_df.at[i, "Descrição"] = nova_descricao
                    recorrentes_df.at[i, "Valor"] = novo_valor
                    recorrentes_df.at[i, "Frequência"] = nova_frequencia
                    recorrentes_df.at[i, "Dia Vencimento"] = novo_dia_vencimento
                    recorrentes_df.at[i, "Próximo Vencimento"] = pd.Timestamp(nova_prox_data)
                    
                    # Salvar as alterações
                    recorrentes_df.to_csv(RECORRENTES_FILE, index=False)
                    st.success(f"✅ Conta recorrente atualizada com sucesso!")
                    
                    # Sair do modo de edição
                    if 'editar_recorrente' in st.session_state:
                        del st.session_state['editar_recorrente']
                    if 'indice_recorrente' in st.session_state:
                        del st.session_state['indice_recorrente']
                    
                    st.rerun()
                
                if cancelar:
                    # Sair do modo de edição sem salvar
                    if 'editar_recorrente' in st.session_state:
                        del st.session_state['editar_recorrente']
                    if 'indice_recorrente' in st.session_state:
                        del st.session_state['indice_recorrente']
                    st.rerun()
    else:
        st.info("Não há contas recorrentes cadastradas. Use o formulário acima para adicionar.")

with tab5:
    st.subheader("🏭 Serviços Cofap/Marelli")
    
    # Botões para adicionar serviço, pedido de compra ou exportar
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("➕ Adicionar Serviço Prestado", key="btn_add_servico", use_container_width=True):
            st.session_state['adicionar_servico'] = True
            st.session_state['tipo_entrada'] = 'servico'
            st.rerun()
    with col2:
        if st.button("💵 Adicionar Pedido de Compra", key="btn_add_pedido", use_container_width=True):
            st.session_state['adicionar_servico'] = True
            st.session_state['tipo_entrada'] = 'pedido'
            st.rerun()
    with col3:
        # Substitua este código na parte de exportação para PDF na aba Serviços Cofap
        if st.button("📄 Exportar para PDF", key="btn_export", use_container_width=True):
            # Criar PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Adicionar título
            pdf.cell(200, 10, txt="Relatório de Serviços Cofap/Marelli", ln=True, align='C')
            pdf.ln(10)
            
            # Adicionar data de geração
            pdf.cell(200, 10, txt=f"Gerado em: {datetime.date.today().strftime('%d/%m/%Y')}", ln=True)
            pdf.ln(10)
            
            # Definir larguras das colunas
            col_width = 190 / 6  # 6 colunas no total
            
            # Cabeçalhos
            pdf.set_font("Arial", 'B', 10)
            headers = ["Funcionário", "Equipamento", "Data", "Valor diária", "Pedido", "Situação"]
            for header in headers:
                pdf.cell(col_width, 10, header, border=1)
            pdf.ln()
            
            # Dados
            pdf.set_font("Arial", size=8)
            for _, row in servicos_df.sort_values('Dia').iterrows():
                # Funcionário
                pdf.cell(col_width, 10, str(row['Funcionario']) if pd.notna(row['Funcionario']) else "", border=1)
                # Equipamento
                pdf.cell(col_width, 10, str(row['Equipamento']) if pd.notna(row['Equipamento']) else "", border=1)
                # Data
                if pd.notna(row['Dia']):
                    data_str = pd.to_datetime(row['Dia']).strftime('%d/%m/%Y')
                else:
                    data_str = ""
                pdf.cell(col_width, 10, data_str, border=1)
                # Valor diária
                if pd.notna(row['Valor diaria']):
                    pdf.cell(col_width, 10, f"R$ {row['Valor diaria']:,.2f}", border=1)
                else:
                    pdf.cell(col_width, 10, "", border=1)
                # Pedido de compra
                pdf.cell(col_width, 10, str(row['Pedidos de compra']) if pd.notna(row['Pedidos de compra']) else "", border=1)
                # Situação
                pdf.cell(col_width, 10, f"R$ {row['Situação']:,.2f}", border=1)
                pdf.ln()
            
            # Método 1: Salvar em arquivo temporário e depois ler
            temp_file = "temp_servicos.pdf"
            pdf.output(temp_file)
            
            # Ler o arquivo temporário
            with open(temp_file, "rb") as file:
                pdf_data = file.read()
            
            # Remover o arquivo temporário
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Oferecer para download
            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf_data,
                file_name=f"servicos_cofap_{datetime.date.today().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf"
            )
    
    # Formulário para adicionar novo serviço ou pedido
    if 'adicionar_servico' in st.session_state and st.session_state['adicionar_servico']:
        tipo_entrada = st.session_state.get('tipo_entrada', 'servico')
        
        with st.form("nova_entrada_cofap"):
            if tipo_entrada == 'servico':
                st.subheader("Adicionar Serviço Prestado")
                
                funcionario = st.selectbox("👷 Funcionário", options=["Richard", "Valter", "Outro"])
                if funcionario == "Outro":
                    funcionario = st.text_input("Nome do funcionário")
                    
                equipamento = st.selectbox("🔧 Equipamento", options=["Empilhadeira", "Munck"])
                
                # Definir automaticamente o valor com base no equipamento
                valor_diaria = 4000.0 if equipamento == "Empilhadeira" else 6000.0
                
                dia = st.date_input("📅 Data do Serviço")
                
                # Calcular nova situação (último valor - valor da diária)
                ultima_situacao = 0
                if not servicos_df.empty:
                    ultima_situacao = servicos_df.sort_values('Dia').iloc[-1]['Situação']
                
                nova_situacao = ultima_situacao - valor_diaria
                
                # Mostrar campos informativos
                st.info(f"Valor da diária: R$ {valor_diaria:,.2f}")
                st.info(f"Saldo atual: R$ {ultima_situacao:,.2f}")
                st.info(f"Novo saldo após este serviço: R$ {nova_situacao:,.2f}")
                
                pedido = None
                valor_pedido = None
            else:  # tipo_entrada == 'pedido'
                st.subheader("Adicionar Pedido de Compra (Entrada de Valor)")
                
                funcionario = None
                equipamento = None
                valor_diaria = None
                
                dia = st.date_input("📅 Data do Pedido")
                pedido = st.text_input("🧾 Número do Pedido de Compra (obrigatório)")
                
                valor_pedido = st.number_input("💰 Valor do Pedido (R$) (obrigatório)", min_value=0.0, format="%.2f")
                
                # Calcular nova situação (último valor + valor do pedido)
                ultima_situacao = 0
                if not servicos_df.empty:
                    ultima_situacao = servicos_df.sort_values('Dia').iloc[-1]['Situação']
                
                nova_situacao = ultima_situacao + valor_pedido
                
                # Mostrar campos informativos
                st.info(f"Saldo atual: R$ {ultima_situacao:,.2f}")
                st.info(f"Novo saldo após este pedido: R$ {nova_situacao:,.2f}")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button("💾 Salvar")
            with col2:
                cancel = st.form_submit_button("❌ Cancelar")
                
            if submitted:
                # Validação para pedido de compra
                if tipo_entrada == 'pedido' and not pedido:
                    st.error("O número do pedido de compra é obrigatório")
                else:
                    # Calcular nova situação baseada no tipo de entrada
                    ultima_situacao = 0
                    if not servicos_df.empty:
                        ultima_situacao = servicos_df.sort_values('Dia').iloc[-1]['Situação']
                    
                    if tipo_entrada == 'servico':
                        # Serviço prestado diminui o saldo
                        nova_situacao = ultima_situacao - valor_diaria
                        
                        novo_registro = pd.DataFrame({
                            "Funcionario": [funcionario],
                            "Equipamento": [equipamento],
                            "Dia": [pd.Timestamp(dia)],
                            "Valor diaria": [valor_diaria],
                            "Pedidos de compra": [None],
                            "Situação": [nova_situacao]
                        })
                    else:  # pedido de compra
                        # Pedido de compra aumenta o saldo
                        nova_situacao = ultima_situacao + valor_pedido
                        
                        novo_registro = pd.DataFrame({
                            "Funcionario": [None],
                            "Equipamento": [None],
                            "Dia": [pd.Timestamp(dia)],
                            "Valor diaria": [valor_pedido],  # Armazenar o valor do pedido aqui
                            "Pedidos de compra": [pedido],
                            "Situação": [nova_situacao]
                        })
                    
                    # Concatenar com o DataFrame existente
                    servicos_df = pd.concat([servicos_df, novo_registro], ignore_index=True)
                    # Ordenar por data
                    servicos_df = servicos_df.sort_values('Dia')
                    # Salvar no arquivo
                    servicos_df.to_csv(SERVICOS_FILE, index=False)
                    
                    st.success("✅ Registro adicionado com sucesso!")
                    st.session_state['adicionar_servico'] = False
                    st.rerun()
            
            # Correção para o botão Cancelar
            if cancel:
                st.session_state['adicionar_servico'] = False
                st.rerun()
    
    # Inicializar a lista de registros selecionados na session_state, se não existir
    if 'registros_selecionados' not in st.session_state:
        st.session_state['registros_selecionados'] = []
        
    # Exibir a tabela de serviços com caixas de seleção
    if not servicos_df.empty:
        # Ordenar por data
        servicos_df_ordenado = servicos_df.sort_values('Dia').reset_index().copy()
        
        # Criar uma tabela editável
        selecionados = []
        
        # Criar colunas formatadas para exibição
        servicos_df_ordenado['Data'] = servicos_df_ordenado['Dia'].dt.strftime('%d/%m/%Y')
        
        # Formatar valores monetários
        servicos_df_ordenado['Valor'] = servicos_df_ordenado['Valor diaria'].apply(
            lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "")
        
        servicos_df_ordenado['Status'] = servicos_df_ordenado['Situação'].apply(
            lambda x: f"R$ {x:,.2f}" if pd.notna(x) else "")
        
        servicos_df_ordenado['Cor Status'] = servicos_df_ordenado['Situação'].apply(
            lambda x: 'red' if x < 0 else 'green')
        
        # Criar uma coluna temporária com informação se é serviço ou pedido
        servicos_df_ordenado['Tipo'] = servicos_df_ordenado['Pedidos de compra'].apply(
            lambda x: 'Pedido' if pd.notna(x) else 'Serviço')
        
        # Criar a tabela com checkboxes
        st.markdown("### Selecione os registros para excluir:")
        
        for idx, row in servicos_df_ordenado.iterrows():
            # Criar uma chave única para cada checkbox
            checkbox_key = f"checkbox_{idx}_{hash(str(row['Dia']))}"
            
            # Criar container para cada linha
            with st.container():
                cols = st.columns([0.5, 2.5, 1.5, 1.5])
                
                # Coluna 1: Checkbox
                with cols[0]:
                    selected = st.checkbox("", key=checkbox_key)
                    if selected:
                        selecionados.append(row['index'])
                
                # Coluna 2: Data e detalhes
                with cols[1]:
                    if row['Tipo'] == 'Pedido':
                        st.write(f"📅 {row['Data']} - 💵 Pedido: {row['Pedidos de compra']}")
                    else:
                        st.write(f"📅 {row['Data']} - 👷 {row['Funcionario']} - 🔧 {row['Equipamento']}")
                
                # Coluna 3: Valor
                with cols[2]:
                    st.write(f"Valor: {row['Valor']}")
                
                # Coluna 4: Situação (com cor)
                with cols[3]:
                    cor = row['Cor Status']
                    st.markdown(f"Situação: <span style='color:{cor}'>{row['Status']}</span>", unsafe_allow_html=True)
        
        # Armazenar os selecionados no session_state
        st.session_state['registros_selecionados'] = selecionados
        
        # Botão para excluir registros selecionados
        if len(selecionados) > 0:
            if st.button(f"🗑️ Excluir {len(selecionados)} registro(s) selecionado(s)", key="btn_excluir_selecionados"):
                st.session_state['confirmar_exclusao_multipla'] = True
                st.rerun()
        
        # Confirmação de exclusão múltipla
        if 'confirmar_exclusao_multipla' in st.session_state and st.session_state['confirmar_exclusao_multipla']:
            indices = st.session_state['registros_selecionados']
            
            st.warning(f"⚠️ Você tem certeza que deseja excluir {len(indices)} registro(s)?")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ Confirmar Exclusão", key="btn_confirm_delete_multi"):
                    # Excluir os registros selecionados
                    servicos_df = servicos_df.drop(indices).reset_index(drop=True)
                    
                    # Recalcular a situação para todos os registros
                    if not servicos_df.empty:
                        saldo = 0
                        servicos_df = servicos_df.sort_values('Dia')
                        
                        for idx, row in servicos_df.iterrows():
                            if pd.notna(row['Pedidos de compra']):
                                # É um pedido de compra, então adiciona ao saldo
                                saldo += row['Valor diaria']
                            else:
                                # É um serviço, então subtrai do saldo
                                saldo -= row['Valor diaria']
                            
                            # Atualiza a situação
                            servicos_df.at[idx, 'Situação'] = saldo
                    
                    # Salvar no arquivo
                    servicos_df.to_csv(SERVICOS_FILE, index=False)
                    
                    st.success(f"✅ {len(indices)} registro(s) excluído(s) com sucesso!")
                    st.session_state.pop('confirmar_exclusao_multipla', None)
                    st.session_state['registros_selecionados'] = []
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancelar Exclusão", key="btn_cancel_delete_multi"):
                    st.session_state.pop('confirmar_exclusao_multipla', None)
                    st.rerun()
    else:
        st.info("Não há serviços registrados. Adicione serviços ou pedidos de compra para começar.")



        
       
# Adicionando instruções de instalação de dependências
st.sidebar.title("Sobre o Sistema")
st.sidebar.markdown("""

### Desenvolvido por:
Nathan Vieira
""")

