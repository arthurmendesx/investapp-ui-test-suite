from playwright.sync_api import Page, expect

from pages.navbar_component import NavbarComponent
from pages.portfolio_page import PortfolioPage


def test_cadastrar_novo_aporte_carteira(
    logged_page: Page,
    navbar: NavbarComponent,
    portfolio_page: PortfolioPage,
):
    """Cadastra um aporte e confere que a linha aparece na tabela."""
    navbar.navegar_para_carteira()

    dias_inv = "0"
    dias_plan = "365"

    portfolio_page.cadastrar_aporte(
        ativo="Poupança",
        quantidade="2500.00",
        preco="1.00",
        dias_inv=dias_inv,
        dias_plan=dias_plan,
    )

    linha = portfolio_page.obter_linha_por_ativo_e_prazo(
        "Poupança", dias_inv, dias_plan
    )
    expect(linha).to_be_visible(timeout=5000)
    expect(linha).to_contain_text("Poupança")