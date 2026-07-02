from jinja2 import Environment, FileSystemLoader
import os

class PDFService:
    @staticmethod
    def generate_html(report_data: dict) -> str:
        # Simplified HTML template
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; }}
                .section {{ margin-top: 30px; }}
                .score {{ font-size: 24px; font-weight: bold; color: #2980b9; }}
                .rec {{ background: #f9f9f9; padding: 10px; border-left: 5px solid #27ae60; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rapport de Gouvernance Pulse IA</h1>
                <p>Version: {report_data.get('version', '1.0')}</p>
            </div>

            <div class="section">
                <h2>Synthèse Exécutive</h2>
                <p>{report_data.get('content', {}).get('executive_summary')}</p>
            </div>

            <div class="section">
                <h2>Scores de Maturité</h2>
                <p>Maturité: <span class="score">{report_data.get('content', {}).get('results', {}).get('maturity_avg', 0):.2f}</span></p>
                <p>Sentiment: <span class="score">{report_data.get('content', {}).get('results', {}).get('sentiment_avg', 0):.2f}</span></p>
                <p>Activation: <span class="score">{report_data.get('content', {}).get('results', {}).get('activation_avg', 0):.2f}</span></p>
            </div>

            <div class="section">
                <h2>Recommandations Stratégiques</h2>
                """
        for rec in report_data.get('content', {}).get('recommendations', []):
            html += f"""
                <div class="rec">
                    <h3>{rec['title']} (Cible: {rec['target']})</h3>
                    <p>{rec['content']}</p>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def export_pdf(report_data: dict, output_path: str):
        html_content = PDFService.generate_html(report_data)
        # In a real environment, we would use Playwright to render this HTML to PDF
        # For now, we'll save the HTML as a placeholder
        with open(output_path, "w") as f:
            f.write(html_content)
        return output_path
