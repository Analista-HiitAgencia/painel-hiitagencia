# 📊 HiitAgência · Painel de Redes Sociais

Ferramenta interna para acompanhar o desempenho dos artistas nas redes
sociais (Instagram, e futuramente Facebook, YouTube e TikTok), com filtro
por **região** e por **período**, mostrando o **crescimento em %**.

Feita para ser operada por **qualquer colaborador**, sem conhecimento de
programação: é só escolher nos menus.

---

## ▶️ Como abrir o painel (uso do dia a dia)

1. Dê **2 cliques** no arquivo **`INICIAR.bat`**.
2. Vai abrir uma janela preta (é normal) e, em seguida, o painel abre
   sozinho em uma **janela própria** (fora do navegador).
3. Use os menus da lateral esquerda para escolher **artista**,
   **estado**, **mesorregião** e **período**.
4. Para **fechar**, feche a janela do painel e depois a janela preta.

> Na **primeira vez** demora alguns minutos (ele prepara tudo sozinho).
> Nas próximas vezes abre em segundos.

---

## 🧪 Modo demonstração x 🔗 Modo real

- A ferramenta já vem funcionando em **modo demonstração**: os números são
  **simulados**, só para você ver o painel e treinar a equipe.
- Para usar **dados reais**, é preciso configurar as chaves de API (abaixo).

### Como ligar os dados reais

1. Faça uma **cópia** do arquivo `.env.example` e renomeie a cópia para
   **`.env`** (só isso, "ponto env").
2. Abra o `.env` no Bloco de Notas e preencha:
   - `MODO_DADOS=real`
   - `META_ACCESS_TOKEN="..."` (token da Meta)
   - `IG_BUSINESS_ID_BAILACO="..."` (ID da conta do Instagram do artista)
3. Salve e abra o painel de novo pelo `INICIAR.bat`.

> As chaves de API são geradas nas contas de desenvolvedor de cada
> plataforma (Meta for Developers, etc.). Como vocês são administradores das
> contas, esse acesso é gratuito. Peça ajuda para gerar os tokens — é uma
> etapa que se faz uma vez.

⚠️ **NUNCA** compartilhe o arquivo `.env` preenchido: ele é a "senha" de
acesso às contas.

---

## ➕ Como crescer a ferramenta (para quem for mexer no código)

Tudo foi pensado para **escalar por configuração**, sem reescrever o
programa:

| O que você quer fazer | Onde mexer |
|---|---|
| Adicionar um **artista novo** | `src/config/artists.py` |
| Ligar uma **rede** de um artista (Facebook, YouTube, TikTok) | `src/config/artists.py` (campo `ativo`) |
| Criar/editar uma **região** ou suas **cidades** | `src/config/regions.py` |
| Adicionar o **conector real** de uma nova rede | criar arquivo em `src/connectors/` e registrar em `src/connectors/loader.py` |

---

## 🗂️ Estrutura do projeto (resumo)

```
INICIAR.bat            <- clique aqui para abrir o painel
app.py                 <- a tela do painel
.env.example           <- modelo das chaves de API (copie para .env)
requirements.txt       <- lista de componentes (instalados sozinhos)
src/
  config/              <- artistas, regiões e configurações
  connectors/          <- ligações com cada rede (demo + reais)
  core/                <- cálculos (crescimento, períodos, formatação)
```

---

## ❓ Problemas comuns

- **"Python não encontrado"** ao abrir o `.bat`: instale o Python 3.12 e
  tente de novo.
- **Erro ao buscar dados reais**: confira se o `.env` está preenchido
  corretamente e se o token não expirou.
- Ainda em dúvida? Volte para o **modo demonstração** (`MODO_DADOS=demo`)
  para confirmar que o painel em si está funcionando.
