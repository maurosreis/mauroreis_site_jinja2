# check_redirects.py
"""
===================================================================
Verificador de Redirecionamentos de URL (check_redirects.py)
===================================================================

Objetivo:
---------
Este script é uma ferramenta de linha de comando (CLI) independente
para diagnosticar e exibir a cadeia completa de redirecionamentos
de uma URL. É especialmente útil para confirmar se redirecionamentos
301 (permanentes) estão configurados corretamente, uma tarefa
essencial para SEO e para garantir a consistência de domínios
(ex: 'www' vs. 'não-www', 'http' vs. 'https').

Como Usar:
-----------
O script deve ser executado a partir do terminal, passando a URL
completa que você deseja verificar como um argumento.

Sintaxe:
  python check_redirects.py <URL_COMPLETA>

Exemplos de Uso:
  
  # Para verificar o redirecionamento de www para não-www
  python check_redirects.py http://www.mauroreis.app

  # Para verificar o redirecionamento de uma página específica
  python check_redirects.py http://www.mauroreis.app/pesquisa/

Dependências:
-------------
- requests: Para fazer as requisições HTTP.
  (Certifique-se de que está listado em seu requirements.txt)

O que o script faz:
-------------------
1.  Recebe uma URL como argumento.
2.  Faz uma requisição HTTP GET para essa URL, permitindo que os
    redirecionamentos ocorram.
3.  Imprime cada passo da cadeia de redirecionamento, incluindo o
    código de status (ex: 301 Moved Permanently) e a URL de destino.
4.  Exibe a URL final e o status final (ex: 200 OK) após todos os
    redirecionamentos serem resolvidos.
5.  Trata erros comuns de rede, como timeouts ou loops de
    redirecionamento.

"""
# check_redirects.py
import requests
import argparse

def trace_redirects(url_to_check):
    """
    Verifica e exibe a cadeia de redirecionamentos de uma URL, mostrando o status
    de cada passo.
    """
    try:
        # Define um User-Agent para simular um navegador comum, o que pode evitar bloqueios simples.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"\n🔎 Verificando redirecionamentos para: {url_to_check}\n")
        
        # Faz a requisição. A biblioteca 'requests' segue os redirecionamentos por padrão
        # e armazena o histórico em `r.history`.
        r = requests.get(url_to_check, headers=headers, allow_redirects=True, timeout=15)
        
        if r.history:
            print("--- Cadeia de Redirecionamentos ---")
            # Itera sobre cada passo do redirecionamento
            for i, resp in enumerate(r.history, 1):
                print(f"{i}. Redirecionamento de: {resp.url}")
                # Imprime o status do redirecionamento (ex: 301, 302)
                print(f"   -> Status: {resp.status_code} {resp.reason}")
                # Imprime para onde o redirecionamento aponta (cabeçalho Location)
                if 'Location' in resp.headers:
                    print(f"   -> Para:   {resp.headers['Location']}")
                print("-" * 20)
            
            print("\n--- Página Final ---")
            print(f"URL Final: {r.url}")
            print(f"-> Status Final: {r.status_code} OK")
        
        else:
            print("✅ Não houve redirecionamentos.")
            print(f"URL Final: {r.url}")
            print(f"-> Status: {r.status_code} {r.reason}")

    except requests.exceptions.Timeout:
        print(f"❌ Erro: Timeout. A requisição para '{url_to_check}' demorou muito para responder.")
    except requests.exceptions.TooManyRedirects:
        print(f"❌ Erro: TooManyRedirects. A URL '{url_to_check}' provavelmente entrou em um loop de redirecionamento.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de Requisição para '{url_to_check}': {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verifica e exibe a cadeia de redirecionamentos de uma URL. Útil para confirmar redirecionamentos 301.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "url",
        help="A URL completa que você deseja verificar (ex: http://www.meusite.com)."
    )
    
    args = parser.parse_args()
    
    trace_redirects(args.url)