from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class AssetManagerPage(BasePage):
    """Representa a aba Gerenciar Taxas (AssetManager.jsx - US05).

    Estrutura real de cada linha da tabela:
    td[0] Ativo | td[1] Categoria | td[2] Taxa Anual Salva ("6.17% a.a.")
    td[3] input de Nova Taxa | td[4] botão "Salvar Alteração"
    Apenas a tabela possui data-testid; campos e botões são localizados
    pela estrutura da linha e pelo papel/nome acessível.
    """

    CABECALHOS = [
        "Ativo",
        "Categoria",
        "Taxa Anual Salva (% a.a.)",
        "Nova Taxa (% a.a.)",
        "Ação",
    ]

    def __init__(self, page: Page):
        super().__init__(page)
        self.tabela_taxas = page.locator("[data-testid='table-asset-rates']")
        self.cabecalhos_tabela = self.tabela_taxas.locator("thead th")
        self.linhas_tabela_taxas = self.tabela_taxas.locator("tbody tr")

    # ---------- Localizadores ----------
    def obter_linha_por_ativo(self, nome_ativo: str) -> Locator:
        """Linha cujo nome do ativo é exatamente igual (evita que 'CDB'
        case com 'CDB Banco X')."""
        return self.linhas_tabela_taxas.filter(
            has=self.page.get_by_role("cell", name=nome_ativo, exact=True)
        )

    def taxa_salva_do_ativo(self, nome_ativo: str) -> Locator:
        """Célula 'Taxa Anual Salva' (ex.: '6.17% a.a.')."""
        return self.obter_linha_por_ativo(nome_ativo).locator("td").nth(2)

    def campo_taxa_do_ativo(self, nome_ativo: str) -> Locator:
        return self.obter_linha_por_ativo(nome_ativo).locator("input")

    def _botao_salvar(self, nome_ativo: str) -> Locator:
        return self.obter_linha_por_ativo(nome_ativo).get_by_role(
            "button", name="Salvar Alteração"
        )

    # ---------- Ações ----------
    def aguardar_tabela_carregada(self):
        """A tabela é preenchida após uma chamada à API (GET /api/assets)."""
        self.tabela_taxas.wait_for(state="visible")
        self.linhas_tabela_taxas.first.wait_for(state="visible")

    def total_de_ativos_listados(self) -> int:
        self.aguardar_tabela_carregada()
        return self.linhas_tabela_taxas.count()

    def obter_taxa_atual(self, nome_ativo: str) -> str:
        """Valor atual do campo de taxa (ex.: '6.66')."""
        campo = self.campo_taxa_do_ativo(nome_ativo)
        campo.wait_for(state="visible")
        return campo.input_value()

    def alterar_taxa(self, nome_ativo: str, nova_taxa: str):
        """Preenche a nova taxa e clica em Salvar Alteração na linha."""
        campo = self.campo_taxa_do_ativo(nome_ativo)
        campo.wait_for(state="visible")
        campo.fill(nova_taxa)
        self._botao_salvar(nome_ativo).click()

    def salvar_taxa_aguardando_api(self, nome_ativo: str, nova_taxa: str):
        """Altera a taxa e devolve a resposta do PUT /api/assets."""
        with self.page.expect_response(
            lambda r: r.request.method == "PUT" and "/api/assets" in r.url
        ) as info:
            self.alterar_taxa(nome_ativo, nova_taxa)
        return info.value

    @staticmethod
    def formatar_taxa_salva(taxa: str) -> str:
        """Formato exibido na coluna 'Taxa Anual Salva'."""
        return f"{float(taxa):.2f}% a.a."
