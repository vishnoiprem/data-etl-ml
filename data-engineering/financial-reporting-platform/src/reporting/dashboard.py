''# src/reporting/dashboard.py
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import os

class DashboardGenerator:
    """Generate interactive dashboards and reports"""

    def __init__(self):
        self.template = "plotly_white"

    def create_html_dashboard(self, gold_data: dict, output_path: str = "output/dashboard.html") -> str:
        """Create HTML dashboard with Plotly"""

        if not gold_data:
            return "No data available for dashboard"

        # Create figures
        figures = []

        # 1. Executive Summary Table
        if 'executive_summary' in gold_data:
            fig1 = self._create_summary_table(gold_data['executive_summary'])
            figures.append(fig1)

        # 2. Revenue by Country
        if 'monthly_metrics' in gold_data:
            fig2 = self._create_revenue_chart(gold_data['monthly_metrics'])
            figures.append(fig2)

            fig3 = self._create_metrics_trend(gold_data['monthly_metrics'])
            figures.append(fig3)

        # 3. Variance Analysis
        if 'variance_analysis' in gold_data:
            fig4 = self._create_variance_chart(gold_data['variance_analysis'])
            figures.append(fig4)

        # 4. Data Quality Overview
        fig5 = self._create_data_quality_chart()
        figures.append(fig5)

        # Combine all figures into one HTML
        html_content = "<!DOCTYPE html>\n<html>\n<head>\n"
        html_content += "<title>Financial Reporting Dashboard</title>\n"
        html_content += "<style>\n"
        html_content += "body { font-family: Arial, sans-serif; margin: 20px; }\n"
        html_content += ".header { text-align: center; margin-bottom: 30px; }\n"
        html_content += ".chart { margin: 20px 0; border: 1px solid #ddd; padding: 10px; }\n"
        html_content += "</style>\n"
        html_content += "</head>\n<body>\n"

        html_content += "<div class='header'>\n"
        html_content += "<h1>Financial Reporting Dashboard</h1>\n"
        html_content += f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>\n"
        html_content += "</div>\n"

        for i, fig in enumerate(figures):
            html_content += f"<div class='chart' id='chart{i}'>\n"
            html_content += fig.to_html(full_html=False, include_plotlyjs='cdn')
            html_content += "</div>\n"

        html_content += "</body>\n</html>"

        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    def _create_summary_table(self, summary_df: pd.DataFrame) -> go.Figure:
        """Create executive summary table"""

        # Prepare table data
        headers = ['Country', 'Revenue', 'COGS', 'Gross Profit', 'Gross Margin', 'Net Profit', 'Net Margin']
        values = []

        for _, row in summary_df.iterrows():
            country = row.get('country_key', 'Unknown')
            revenue = row.get('REVENUE', 0)
            cogs = row.get('COGS', 0)
            expenses = row.get('EXPENSE', 0)
            gross_profit = row.get('gross_profit', 0)
            net_profit = row.get('net_profit', 0)

            gross_margin = row.get('gross_margin_pct', 0)
            net_margin = row.get('net_margin_pct', 0)

            values.append([
                country,
                f"${revenue:,.0f}",
                f"${cogs:,.0f}",
                f"${gross_profit:,.0f}",
                f"{gross_margin:.1f}%" if not pd.isna(gross_margin) else "N/A",
                f"${net_profit:,.0f}",
                f"{net_margin:.1f}%" if not pd.isna(net_margin) else "N/A"
            ])

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=headers,
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=list(zip(*values)) if values else [[]]*len(headers),
                fill_color='lavender',
                align='left',
                font=dict(size=11)
            )
        )])

        fig.update_layout(
            title="Executive Summary",
            height=300
        )

        return fig

    def _create_revenue_chart(self, metrics_df: pd.DataFrame) -> go.Figure:
        """Create revenue by country chart"""

        revenue_data = metrics_df[metrics_df['account_category'] == 'REVENUE']

        if revenue_data.empty:
            fig = go.Figure()
            fig.add_annotation(text="No revenue data available", showarrow=False)
            fig.update_layout(title="Revenue by Country", height=400)
            return fig

        # Aggregate by country and month
        revenue_pivot = revenue_data.pivot_table(
            index=['year', 'month'],
            columns='country_key',
            values='total_amount_usd',
            aggfunc='sum'
        ).reset_index()

        revenue_pivot['period'] = revenue_pivot['year'].astype(str) + '-' + revenue_pivot['month'].astype(str).str.zfill(2)

        fig = go.Figure()

        for country in revenue_pivot.columns:
            if country not in ['year', 'month', 'period']:
                fig.add_trace(go.Bar(
                    name=str(country),
                    x=revenue_pivot['period'],
                    y=revenue_pivot[country],
                    text=revenue_pivot[country].apply(lambda x: f"${x:,.0f}"),
                    textposition='auto',
                ))

        fig.update_layout(
            title="Monthly Revenue by Country",
            xaxis_title="Period",
            yaxis_title="Revenue (USD)",
            barmode='group',
            height=400,
            template=self.template
        )

        return fig

    def _create_metrics_trend(self, metrics_df: pd.DataFrame) -> go.Figure:
        """Create trend chart for key metrics"""

        # Filter for key metrics
        key_metrics = metrics_df[metrics_df['account_category'].isin(['REVENUE', 'COGS', 'EXPENSE'])]

        if key_metrics.empty:
            fig = go.Figure()
            fig.add_annotation(text="No trend data available", showarrow=False)
            fig.update_layout(title="Key Metrics Trend", height=400)
            return fig

        key_metrics['period'] = key_metrics['year'].astype(str) + '-' + key_metrics['month'].astype(str).str.zfill(2)

        fig = px.line(
            key_metrics,
            x='period',
            y='total_amount_usd',
            color='account_category',
            markers=True,
            title="Key Metrics Trend Over Time"
        )

        fig.update_layout(
            xaxis_title="Period",
            yaxis_title="Amount (USD)",
            height=400,
            template=self.template
        )

        return fig

    def _create_variance_chart(self, variance_df: pd.DataFrame) -> go.Figure:
        """Create variance analysis chart"""

        if variance_df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No variance data available", showarrow=False)
            fig.update_layout(title="Variance Analysis", height=400)
            return fig

        # Filter significant variances
        significant = variance_df[
            variance_df['percentage_variance'].abs() > 10
        ]

        if significant.empty:
            fig = go.Figure()
            fig.add_annotation(text="No significant variances detected", showarrow=False)
            fig.update_layout(title="Variance Analysis", height=400)
            return fig

        fig = px.bar(
            significant,
            x='account_category',
            y='percentage_variance',
            color='country_key',
            barmode='group',
            title="Significant Variances (>10%)",
            text='percentage_variance'
        )

        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            xaxis_title="Account Category",
            yaxis_title="Variance (%)",
            height=400,
            template=self.template
        )

        return fig

    def _create_data_quality_chart(self) -> go.Figure:
        """Create data quality chart"""

        # Read quality report if exists
        quality_report_path = "reports/quality_report.json"
        if os.path.exists(quality_report_path):
            import json
            with open(quality_report_path, 'r') as f:
                report = json.load(f)

            sources = list(report.get('sources', {}).keys())
            scores = [report['sources'][source].get('score', 0) * 100 for source in sources]
        else:
            sources = ['Overall']
            scores = [95]

        fig = go.Figure(data=[
            go.Bar(
                x=sources,
                y=scores,
                text=[f"{s:.1f}%" for s in scores],
                textposition='auto',
                marker_color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
            )
        ])

        fig.update_layout(
            title="Data Quality Scores",
            xaxis_title="Data Source",
            yaxis_title="Quality Score (%)",
            yaxis_range=[0, 100],
            height=300,
            template=self.template
        )

        return fig

    def export_to_excel(self, gold_data: dict, output_path: str = "output/financial_report.xlsx"):
        """Export data to Excel file"""

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Export key tables
            for table_name, df in gold_data.items():
                if not df.empty:
                    sheet_name = table_name[:31]  # Excel sheet name limit
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Add summary worksheet
            if 'executive_summary' in gold_data:
                summary_df = gold_data['executive_summary']
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

        print(f"Excel report saved to {output_path}")