import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader
import os

class PDFService:
    @staticmethod
    def generate_html(report_data: dict, template_name: str) -> str:
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(f"{template_name}.html")

        return template.render(
            **report_data,
            now=datetime.now().strftime('%d/%m/%Y %H:%M'),
            methodology=report_data.get("methodology_snapshot", {"version": "Unknown"})
        )

    @staticmethod
    async def export_pdf(report_data: dict, output_path: str, template_name: str = "direction_report"):
        html_content = PDFService.generate_html(report_data, template_name)

        async with async_playwright() as p:
            browser = await p.chromium.launch(args=["--no-sandbox"])
            page = await browser.new_page()
            await page.set_content(html_content)
            # Wait for content to render if needed
            await page.pdf(path=output_path, format="A4", print_background=True)
            await browser.close()

        return output_path

def run_export_sync(report_data: dict, output_path: str, template_name: str = "direction_report"):
    """Utility to run the async export in a sync context."""
    return asyncio.run(PDFService.export_pdf(report_data, output_path, template_name))
