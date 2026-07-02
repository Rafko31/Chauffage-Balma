import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader
import os

class PDFService:
    @staticmethod
    def generate_html(report_data: dict) -> str:
        # Improved HTML template with better styling
        html = f"""
        <html>
        <head>
            <style>
                @page {{ margin: 2cm; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ text-align: center; border-bottom: 3px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px; }}
                .header h1 {{ color: #2c3e50; margin: 0; text-transform: uppercase; letter-spacing: 2px; }}
                .section {{ margin-top: 40px; page-break-inside: avoid; }}
                .section h2 {{ color: #2980b9; border-left: 5px solid #2980b9; padding-left: 15px; }}
                .score-box {{ background: #f4f7f6; padding: 20px; border-radius: 8px; display: flex; justify-content: space-around; }}
                .score-item {{ text-align: center; }}
                .score-val {{ font-size: 32px; font-weight: bold; color: #2c3e50; display: block; }}
                .score-label {{ font-size: 14px; color: #7f8c8d; text-transform: uppercase; }}
                .rec {{ background: #fff; padding: 15px; border: 1px solid #e0e0e0; border-left: 5px solid #27ae60; margin-bottom: 15px; border-radius: 4px; }}
                .rec h3 {{ margin-top: 0; color: #27ae60; }}
                .footer {{ position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 10px; color: #bdc3c7; border-top: 1px solid #ecf0f1; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport de Gouvernance Pulse IA</h1>
                <p>Manufacture Innovante Inc. | Version {report_data.get('version', '1.0')}</p>
            </div>

            <div class="section">
                <h2>Synthèse Exécutive</h2>
                <p>{report_data.get('content', {}).get('executive_summary')}</p>
            </div>

            <div class="section">
                <h2>Indicateurs de Performance</h2>
                <div class="score-box">
                    <div class="score-item">
                        <span class="score-val">{report_data.get('content', {}).get('results', {}).get('maturity_avg', 0):.2f}</span>
                        <span class="score-label">Maturité</span>
                    </div>
                    <div class="score-item">
                        <span class="score-val">{report_data.get('content', {}).get('results', {}).get('sentiment_avg', 0):.2f}</span>
                        <span class="score-label">Sentiment</span>
                    </div>
                    <div class="score-item">
                        <span class="score-val">{report_data.get('content', {}).get('results', {}).get('activation_avg', 0):.2f}</span>
                        <span class="score-label">Activation</span>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>Recommandations Stratégiques</h2>
                """
        for rec in report_data.get('content', {}).get('recommendations', []):
            html += f"""
                <div class="rec">
                    <h3>{rec['title']}</h3>
                    <p><strong>Cible :</strong> {rec['target']}</p>
                    <p>{rec['content']}</p>
                </div>
            """

        html += f"""
            </div>
            <div class="footer">
                Généré par Pulse IA - Le {datetime.now().strftime('%d/%m/%Y %H:%M')} | Document Immuable Ref: {report_data.get('id')}
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    async def export_pdf(report_data: dict, output_path: str):
        html_content = PDFService.generate_html(report_data)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content)
            await page.pdf(path=output_path, format="A4", print_background=True)
            await browser.close()

        return output_path

def run_export_sync(report_data: dict, output_path: str):
    """Utility to run the async export in a sync context."""
    return asyncio.run(PDFService.export_pdf(report_data, output_path))
