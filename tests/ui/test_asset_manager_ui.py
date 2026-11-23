import re
from playwright.sync_api import Page, expect
from pages.navbar_component import NavbarComponent
from pages.asset_manager_page import AssetManagerPage

# Ativo somente leitura (visualização)
ATIVO_LEITURA = "Poupança"
# Ativo de QA usado na edição (a taxa salva é personalizada por usuário)
ATIVO_EDICAO = "ATIVO_TESTE_UPSERT_QA"
NOVA_TAXA = "7.50"


def test_visualizar_tabela_de_taxas(
    logged_page: Page,
    navbar: NavbarComponent,
    asset_manager_page: AssetManagerPage,
):
    """Valida cabeçalhos, existência de ativos e formato das taxas."""
    navbar.navegar_para_gerenciar_taxas()
    asset_manager_page.aguardar_tabela_carregada()

    expect(asset_manager_page.cabecalhos_tabela).to_have_text(
        AssetManagerPage.CABECALHOS
    )
    assert asset_manager_page.total_de_ativos_listados() > 0
    expect(
        asset_manager_page.obter_linha_por_ativo(ATIVO_LEITURA)
    ).to_be_visible()
    expect(
        asset_manager_page.taxa_salva_do_ativo(ATIVO_LEITURA)
    ).to_have_text(re.compile(r"^\d+\.\d{2}% a\.a\.$"))


def test_alterar_taxa_anual_do_ativo(
    logged_page: Page,
    navbar: NavbarComponent,
    asset_manager_page: AssetManagerPage,
):
    """Altera a taxa pela UI e valida o PUT enviado e a confirmação da API."""
    navbar.navegar_para_gerenciar_taxas()
    asset_manager_page.aguardar_tabela_carregada()
    taxa_original = asset_manager_page.obter_taxa_atual(ATIVO_EDICAO)

    try:
        resposta = asset_manager_page.salvar_taxa_aguardando_api(
            ATIVO_EDICAO, NOVA_TAXA
        )

        corpo = resposta.request.post_data_json
        assert corpo["asset_name"] == ATIVO_EDICAO
        assert corpo["annual_rate"] == float(NOVA_TAXA)
        assert resposta.status == 200
        assert "salva com sucesso" in resposta.text()
    finally:
        asset_manager_page.salvar_taxa_aguardando_api(
            ATIVO_EDICAO, taxa_original
        )


def test_taxa_salva_persiste_na_tabela_apos_recarregar(
    logged_page: Page,
    navbar: NavbarComponent,
    asset_manager_page: AssetManagerPage,
):
    """Após salvar e recarregar, a coluna 'Taxa Anual Salva' deve mostrar
    a nova taxa.

    BUG CONHECIDO: a API confirma o salvamento (PUT 200) e o GET devolve a
    taxa personalizada, mas a tabela continua exibindo a taxa padrão.
    Este teste fica vermelho de propósito para evidenciar o defeito.
    """
    navbar.navegar_para_gerenciar_taxas()
    asset_manager_page.aguardar_tabela_carregada()
    taxa_original = asset_manager_page.obter_taxa_atual(ATIVO_EDICAO)

    try:
        asset_manager_page.salvar_taxa_aguardando_api(ATIVO_EDICAO, NOVA_TAXA)

        asset_manager_page.recarregar()
        expect(navbar.botao_sair).to_be_visible(timeout=10000)
        navbar.navegar_para_gerenciar_taxas()
        asset_manager_page.aguardar_tabela_carregada()

        expect(
            asset_manager_page.taxa_salva_do_ativo(ATIVO_EDICAO)
        ).to_have_text(AssetManagerPage.formatar_taxa_salva(NOVA_TAXA))
    finally:
        asset_manager_page.salvar_taxa_aguardando_api(
            ATIVO_EDICAO, taxa_original
        )
