import json
import os
from datetime import datetime
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from .models import ThreatEvent, GlobalThreatStats


class ThreatMapReportGenerator:
    """Class to generate threat map reports in various formats."""
    
    def __init__(self, threat_events, date_range=None, title="Threat Map Report"):
        self.threat_events = threat_events
        self.date_range = date_range
        self.title = title
    
    def generate_json_report(self):
        """Generate JSON report for threat map data."""
        report_data = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'threat_map',
                'version': '1.0',
                'date_range': self.date_range,
                'title': self.title
            },
            'summary': {
                'total_events': self.threat_events.count(),
                'threat_types': self._get_threat_type_summary(),
                'severity_breakdown': self._get_severity_breakdown(),
                'geographic_distribution': self._get_geographic_summary(),
                'top_countries': self._get_top_countries(),
                'timeline_data': self._get_timeline_data()
            },
            'events': [
                {
                    'id': str(event.id),
                    'threat_type': event.threat_type,
                    'threat_type_display': event.get_threat_type_display(),
                    'severity': event.severity,
                    'severity_display': event.get_severity_display(),
                    'timestamp': event.timestamp.isoformat(),
                    'country': event.country,
                    'city': event.city,
                    'latitude': float(event.latitude) if event.latitude else None,
                    'longitude': float(event.longitude) if event.longitude else None,
                    'description': event.description,
                    'file_name': event.file_name,
                    'file_hash': event.file_hash,
                    'ip_address': event.ip_address
                }
                for event in self.threat_events.order_by('-timestamp')
            ]
        }
        
        return json.dumps(report_data, indent=2)
    
    def generate_pdf_report(self):
        """Generate PDF report for threat map data."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Build the PDF content
        story = []
        
        # Title
        story.append(Paragraph(f"Trojan Defender - {self.title}", title_style))
        story.append(Spacer(1, 20))
        
        # Report info
        report_info = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Report Type:', 'Global Threat Analysis'],
            ['Date Range:', self.date_range or 'All Time'],
            ['Total Events:', str(self.threat_events.count())]
        ]
        
        info_table = Table(report_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkblue))
        story.append(Spacer(1, 10))
        
        summary_data = [
            ['Total Threat Events:', str(self.threat_events.count())],
            ['Unique Countries Affected:', str(len(self._get_geographic_summary()))],
            ['Most Common Threat Type:', self._get_most_common_threat_type()],
            ['Highest Severity Level:', self._get_highest_severity()],
            ['Most Affected Country:', self._get_most_affected_country()]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Threat Type Distribution
        story.append(Paragraph("Threat Type Distribution", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkblue))
        story.append(Spacer(1, 10))
        
        threat_types = self._get_threat_type_summary()
        if threat_types:
            threat_headers = ['Threat Type', 'Count', 'Percentage']
            threat_data = [threat_headers]
            total_threats = sum(threat_types.values())
            
            for threat_type, count in sorted(threat_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_threats * 100) if total_threats > 0 else 0
                threat_data.append([
                    threat_type.replace('_', ' ').title(),
                    str(count),
                    f"{percentage:.1f}%"
                ])
            
            threat_table = Table(threat_data, colWidths=[2*inch, 1*inch, 1*inch])
            threat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(threat_table)
        else:
            story.append(Paragraph("No threat data available for the selected period.", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Geographic Distribution
        story.append(Paragraph("Geographic Distribution", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkblue))
        story.append(Spacer(1, 10))
        
        top_countries = self._get_top_countries(10)
        if top_countries:
            geo_headers = ['Country', 'Threat Count', 'Percentage']
            geo_data = [geo_headers]
            total_events = self.threat_events.count()
            
            for country, count in top_countries:
                percentage = (count / total_events * 100) if total_events > 0 else 0
                geo_data.append([
                    country or 'Unknown',
                    str(count),
                    f"{percentage:.1f}%"
                ])
            
            geo_table = Table(geo_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            geo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(geo_table)
        else:
            story.append(Paragraph("No geographic data available.", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Severity Analysis
        story.append(Paragraph("Severity Analysis", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkblue))
        story.append(Spacer(1, 10))
        
        severity_breakdown = self._get_severity_breakdown()
        if severity_breakdown:
            severity_headers = ['Severity Level', 'Count', 'Percentage']
            severity_data = [severity_headers]
            total_events = sum(severity_breakdown.values())
            
            severity_order = ['critical', 'high', 'medium', 'low']
            for severity in severity_order:
                if severity in severity_breakdown:
                    count = severity_breakdown[severity]
                    percentage = (count / total_events * 100) if total_events > 0 else 0
                    severity_data.append([
                        severity.title(),
                        str(count),
                        f"{percentage:.1f}%"
                    ])
            
            severity_table = Table(severity_data, colWidths=[2*inch, 1*inch, 1*inch])
            severity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(severity_table)
        else:
            story.append(Paragraph("No severity data available.", styles['Normal']))
        
        story.append(Spacer(1, 30))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        story.append(HRFlowable(width="100%", thickness=0.5, lineCap='round', color=colors.grey))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Generated by Trojan Defender Security Platform", footer_style))
        story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _get_threat_type_summary(self):
        """Get summary of threat types."""
        from django.db.models import Count
        return dict(self.threat_events.values('threat_type').annotate(count=Count('threat_type')).values_list('threat_type', 'count'))
    
    def _get_severity_breakdown(self):
        """Get breakdown of threat severities."""
        from django.db.models import Count
        return dict(self.threat_events.values('severity').annotate(count=Count('severity')).values_list('severity', 'count'))
    
    def _get_geographic_summary(self):
        """Get geographic distribution summary."""
        from django.db.models import Count
        return dict(self.threat_events.values('country').annotate(count=Count('country')).values_list('country', 'count'))
    
    def _get_top_countries(self, limit=10):
        """Get top countries by threat count."""
        from django.db.models import Count
        return list(self.threat_events.values('country').annotate(
            count=Count('country')
        ).order_by('-count')[:limit].values_list('country', 'count'))
    
    def _get_timeline_data(self):
        """Get timeline data for threats."""
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        
        return list(self.threat_events.annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date').values_list('date', 'count'))
    
    def _get_most_common_threat_type(self):
        """Get the most common threat type."""
        threat_types = self._get_threat_type_summary()
        if not threat_types:
            return 'N/A'
        return max(threat_types.items(), key=lambda x: x[1])[0].replace('_', ' ').title()
    
    def _get_highest_severity(self):
        """Get the highest severity level found."""
        severity_breakdown = self._get_severity_breakdown()
        if not severity_breakdown:
            return 'N/A'
        
        severity_order = ['critical', 'high', 'medium', 'low']
        for severity in severity_order:
            if severity in severity_breakdown and severity_breakdown[severity] > 0:
                return severity.title()
        return 'N/A'
    
    def _get_most_affected_country(self):
        """Get the most affected country."""
        top_countries = self._get_top_countries(1)
        if not top_countries:
            return 'N/A'
        return top_countries[0][0] or 'Unknown'