import pandas as pd
import random
from datetime import datetime, timedelta

def gerar_dados_licitacoes(num_registros=200):
    # Definindo sementes para reprodutibilidade
    random.seed(42)
    
    orgaos = ["SEIA", "Celepar", "SESA", "SEAP", "CGE", "DETRAN", "SEED", "SETI"]
    
    objetos_ti = [
        "Contratação de Nuvem Híbrida para o Programa Transforma Paraná",
        "Licenciamento de Software de Inteligência Artificial para análise documental",
        "Serviços de Desenvolvimento de Chatbot E-Gov para atendimento ao cidadão",
        "Consultoria especializada para Implantação de IA em Processos Jurídicos",
        "Upgrade de infraestrutura de Servidores do Datacenter Celepar",
        "Desenvolvimento do Novo Portal de Transparência da CGE",
        "Suporte Técnico Especializado para Sistemas de Prontuário Eletrônico da SESA",
        "Conectividade e banda larga para Escolas Estaduais da SEED",
        "Licenciamento de banco de dados corporativo e suporte técnico",
        "Desenvolvimento de sistema de IA para detecção de fraudes em licitações",
        "Aquisição de computadores de alto desempenho e notebooks corporativos",
        "Contratação de consultoria para governança de dados e LGPD",
        "Desenvolvimento de aplicativo móvel para integração de serviços estaduais",
        "Licenciamento de plataforma low-code para automação de processos internos",
        "Serviços de auditoria de segurança da informação e testes de intrusão (Pentest)"
    ]
    
    modalidades = [
        "Pregão Eletrônico",
        "Inexigibilidade de Licitação",
        "Dispensa de Licitação",
        "Diálogo Competitivo",
        "Concorrência Pública"
    ]
    
    situacoes = ["Homologado", "Homologado", "Homologado", "Homologado", "Deserto", "Fracassado", "Revogado", "Em Andamento"]
    
    empresas_tecnologia = [
        ("TechPar Soluções Ltda", "12.345.678/0001-90"),
        ("Inova Sul S.A.", "98.765.432/0001-10"),
        ("Inteligência Global ME", "45.678.901/0001-23"),
        ("Brasil Software EIRELI", "23.456.789/0001-34"),
        ("Datashield Segurança Ltda", "89.012.345/0001-45"),
        ("Consultoria Eficiente S.A.", "56.789.012/0001-56"),
        ("Startups PR Co.", "34.567.890/0001-67")
    ]
    
    dados = []
    
    data_inicio = datetime(2021, 1, 1)
    
    for i in range(num_registros):
        # Número do Processo (e-Protocolo)
        ano_processo = random.randint(21, 26)
        num_seq = random.randint(100000, 999999)
        digito = random.randint(0, 9)
        numero_processo = f"{ano_processo}.{num_seq}-{digito}"
        
        # Órgão Demandante
        orgao = random.choice(orgaos)
        
        # Objeto da Licitação
        objeto = random.choice(objetos_ti)
        # Adicionar uma variação para simular objetos reais
        objeto += f" - Fase {random.randint(1, 3)}"
        
        # Modalidade Licitatória
        # Diálogo Competitivo é mais raro e novo
        pesos_modalidades = [0.65, 0.15, 0.12, 0.03, 0.05]
        modalidade = random.choices(modalidades, weights=pesos_modalidades)[0]
        
        # Valor Máximo Estimado
        valor_maximo = round(random.uniform(30000, 4500000), 2)
        
        # Situação Atual
        situacao = random.choice(situacoes)
        
        # Valor Final Homologado e Vencedor
        if situacao == "Homologado":
            # Desconto médio de licitação
            desconto = random.uniform(0.70, 0.98)
            valor_homologado = round(valor_maximo * desconto, 2)
            empresa, cnpj = random.choice(empresas_tecnologia)
        elif situacao == "Em Andamento":
            valor_homologado = None
            empresa, cnpj = "N/A", "N/A"
        else:
            # Deserto, Fracassado, Revogado
            valor_homologado = 0.0
            empresa, cnpj = "N/A", "N/A"
            
        # Data de Homologação / Evento
        dias_decorridos = random.randint(0, 2000)
        data_evento = data_inicio + timedelta(days=dias_decorridos)
        # Garantir que a data não ultrapasse hoje (junho de 2026)
        if data_evento > datetime(2026, 6, 30):
            data_evento = datetime(2026, 6, 30) - timedelta(days=random.randint(1, 30))
            
        dados.append({
            "Numero_Processo": numero_processo,
            "Orgao_Demandante": orgao,
            "Objeto": objeto,
            "Modalidade": modalidade,
            "Valor_Maximo_Estimado": valor_maximo,
            "Valor_Homologado": valor_homologado,
            "Situacao": situacao,
            "Razao_Social_Vencedora": empresa,
            "CNPJ_Vencedor": cnpj,
            "Data_Evento": data_evento.strftime("%Y-%m-%d")
        })
        
    df = pd.DataFrame(dados)
    # Ordenar por data
    df = df.sort_values(by="Data_Evento", ascending=False)
    
    # Salvar em CSV
    output_path = "licitacoes_tecnologia_pr.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Dataset gerado com sucesso em '{output_path}' com {num_registros} registros.")

if __name__ == "__main__":
    gerar_dados_licitacoes(250)
