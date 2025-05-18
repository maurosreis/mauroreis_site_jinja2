# mauroreis_site_jinja2

Este projeto gera páginas HTML estáticas com conteúdo modular usando o Jinja2 e Python.

## 📁 Estrutura

- `templates/`: Contém os arquivos base e os conteúdos de cada página.
- `public_html/`: Onde os arquivos HTML finais são gerados.
- `build.py`: Script que monta as páginas.
- `requirements.txt`: Lista de dependências do projeto.

## ✅ Como usar

### 1. Crie e ative o ambiente virtual

**No terminal do VSCode ou PowerShell:**

```powershell
python -m venv venv
```

```powershell
# Caso scripts estejam bloqueados, execute no PowerShell (Admin):
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

```powershell
# Agora ative o ambiente:
.env\Scripts\Activate.ps1
```

> No Prompt de Comando (cmd), use:
> ```
> venv\Scriptsctivate.bat
> ```

---

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

---

### 3. Gere as páginas

```bash
python build.py
```

O conteúdo gerado estará na pasta `public_html/`.

---

### 4. Desative o ambiente

```bash
deactivate
```

---

## 🌐 Publicação

Você pode subir o conteúdo da pasta `public_html/` diretamente para qualquer serviço de hospedagem estática, como GitHub Pages, Netlify ou seu próprio servidor.

