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
from .models import ScanResult, ScanThreat


class ReportGenerator:
    """Class to generate scan reports in various formats."""
    
    def __init__(self, scan_result):
        self.scan_result = scan_result
        self.threats = scan_result.threats.all()
    
    def generate_json_report(self):
        """Generate JSON report for a scan result."""
        report_data = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'scan_result',
                'version': '1.0'
            },
            'scan_details': {
                'scan_id': str(self.scan_result.id),
                'file_name': self.scan_result.file_name,
                'file_size': self.scan_result.file_size,
                'file_type': self.scan_result.file_type,
                'file_hash': self.scan_result.file_hash,
                'upload_date': self.scan_result.upload_date.isoformat() if self.scan_result.upload_date else None,
                'scan_date': self.scan_result.scan_date.isoformat() if self.scan_result.scan_date else None,
                'status': self.scan_result.status,
                'status_display': self.scan_result.get_status_display(),
                'threat_level': self.scan_result.threat_level,
                'threat_level_display': self.scan_result.get_threat_level_display(),
                'scan_duration': str(self.scan_result.scan_duration) if self.scan_result.scan_duration else None,
                'user_email': self.scan_result.user.email
            },
            'threats': [
                {
                    'id': str(threat.id),
                    'name': threat.name,
                    'threat_type': threat.threat_type,
                    'threat_type_display': threat.get_threat_type_display(),
                    'description': threat.description,
                    'location': threat.location,
                    'detection_engine': threat.detection_engine,
                    'detection_rule': threat.detection_rule,
                    'severity': threat.severity,
                    'severity_display': threat.get_severity_display()
                }
                for threat in self.threats
            ],
            'summary': {
                'total_threats': self.threats.count(),
                'threat_types': self._get_threat_type_summary(),
                'severity_breakdown': self._get_severity_breakdown(),
                'detection_engines': self._get_detection_engine_summary()
            }
        }
        
        return json.dumps(report_data, indent=2)
    
    def generate_pdf_report(self):
        """Generate PDF report for a scan result."""
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
        story.append(Paragraph("Trojan Defender - Scan Report", title_style))
        story.append(Spacer(1, 20))
        
        # Report info
        report_info = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Report Type:', 'File Scan Analysis'],
            ['Scan ID:', str(self.scan_result.id)]
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
        
        # File Details Section
        story.append(Paragraph("File Details", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkblue))
        story.append(Spacer(1, 10))
        
        file_details = [
            ['File Name:', self.scan_result.file_name],
            ['File Size:', f"{self.scan_result.file_size:,} bytes"],
            ['File Type:', self.scan_result.file_type or 'Unknown'],
            ['SHA-256 Hash:', self.scan_result.file_hash],
            ['Upload Date:', self.scan_result.upload_date.strftime('%Y-%m-%d %H:%M:%S') if self.scan_result.upload_date else 'N/A'],
            ['Scan Date:', self.scan_result.scan_date.strftime('%Y-%m-%d %H:%M:%S') if self.scan_result.scan_date else 'N/A'],
            ['Scan Duration:', str(self.scan_result.scan_duration) if self.scan_result.scan_duration else 'N/A']
        ]
        
        file_table = Table(file_details, colWidths=[2*inch, 4*inch])
        file_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(file_table)
        story.append(Spacer(1, 20))
        
        # Scan Results Section
        story.append(Paragraph("Scan Results", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkblue))
        story.append(Spacer(1, 10))
        
        # Status and threat level
        status_color = colors.green if self.scan_result.threat_level == 'clean' else colors.red
        status_text = f"<font color='{status_color.hexval()}'>Status: {self.scan_result.get_status_display()}</font>"
        threat_text = f"<font color='{status_color.hexval()}'>Threat Level: {self.scan_result.get_threat_level_display()}</font>"
        
        story.append(Paragraph(status_text, styles['Normal']))
        story.append(Paragraph(threat_text, styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Threats Section
        if self.threats.exists():
            story.append(Paragraph("Detected Threats", heading_style))
            story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.red))
            story.append(Spacer(1, 10))
            
            # Threat summary
            summary_data = [
                ['Total Threats:', str(self.threats.count())],
                ['Threat Types:', ', '.join(self._get_threat_type_summary().keys())],
                ['Highest Severity:', self._get_highest_severity()]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 15))
            
            # Detailed threat list
            story.append(Paragraph("Threat Details", ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=14)))
            story.append(Spacer(1, 10))
            
            threat_headers = ['Threat Name', 'Type', 'Severity', 'Engine', 'Location']
            threat_data = [threat_headers]
            
            for threat in self.threats:
                threat_data.append([
                    threat.name[:30] + '...' if len(threat.name) > 30 else threat.name,
                    threat.get_threat_type_display(),
                    threat.get_severity_display(),
                    threat.detection_engine,
                    threat.location[:20] + '...' if len(threat.location) > 20 else threat.location
                ])
            
            threat_table = Table(threat_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
            threat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(threat_table)
        else:
            story.append(Paragraph("No Threats Detected", heading_style))
            story.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.green))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<font color='green'>✓ This file appears to be clean and safe.</font>", styles['Normal']))
        
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
        story.append(Paragraph(f"Report ID: {self.scan_result.id}", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _get_threat_type_summary(self):
        """Get summary of threat types."""
        threat_types = {}
        for threat in self.threats:
            threat_type = threat.get_threat_type_display()
            threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
        return threat_types
    
    def _get_severity_breakdown(self):
        """Get breakdown of threat severities."""
        severities = {}
        for threat in self.threats:
            severity = threat.get_severity_display()
            severities[severity] = severities.get(severity, 0) + 1
        return severities
    
    def _get_detection_engine_summary(self):
        """Get summary of detection engines used."""
        engines = {}
        for threat in self.threats:
            engine = threat.detection_engine
            engines[engine] = engines.get(engine, 0) + 1
        return engines
    
    def _get_highest_severity(self):
        """Get the highest severity level found."""
        if not self.threats.exists():
            return 'None'
        
        severity_order = ['low', 'medium', 'high', 'critical']
        highest = 'low'
        
        for threat in self.threats:
            if threat.severity in severity_order:
                current_index = severity_order.index(threat.severity)
                highest_index = severity_order.index(highest)
                if current_index > highest_index:
                    highest = threat.severity
        
        return highest.title()


class ThreatMapReportGenerator:
    """Class to generate threat map reports."""
    
    def __init__(self, threat_events, date_range=None):
        self.threat_events = threat_events
        self.date_range = date_range
    
    def generate_json_report(self):
        """Generate JSON report for threat map data."""
        report_data = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'threat_map',
                'version': '1.0',
                'date_range': self.date_range
            },
            'summary': {
                'total_events': self.threat_events.count(),
                'threat_types': self._get_threat_type_summary(),
                'severity_breakdown': self._get_severity_breakdown(),
                'geographic_distribution': self._get_geographic_summary(),
                'top_countries': self._get_top_countries()
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
                    'file_hash': event.file_hash
                }
                for event in self.threat_events
            ]
        }
        
        return json.dumps(report_data, indent=2)
    
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