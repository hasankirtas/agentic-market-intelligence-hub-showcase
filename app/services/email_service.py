"""
Email sending service for report notifications.
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from datetime import datetime

from app.core.config import get_settings, Settings
from models.report import Report
from app.database.repositories.report_repository import ReportRepository
from core.logger import setup_logger
from core.resilience.decorators import resilient
from pydantic import EmailStr, ValidationError
from email_validator import validate_email as validate_email_address, EmailNotValidError

logger = setup_logger(__name__)


class EmailService:
    """
    Email service for sending competitive intelligence reports.
    
    Handles SMTP connection, template rendering, and email delivery.
    Integrates with ReportRepository to track email status.
    """
    
    def __init__(
        self,
        report_repository: Optional[ReportRepository] = None,
        settings: Optional[Settings] = None
    ):
        """
        Initialize email service.
        
        Args:
            report_repository: ReportRepository instance (optional, for tracking)
            settings: Settings instance (optional, uses get_settings() if not provided)
        """
        self.settings = settings or get_settings()
        self.report_repository = report_repository
        
        # Initialize Jinja2 environment
        template_dir = Path(self.settings.email_template_dir)
        if not template_dir.exists():
            # Create template directory if it doesn't exist
            template_dir.mkdir(parents=True, exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        
        logger.info(f"EmailService initialized with template dir: {template_dir}")
    
    def _get_smtp_config(self) -> dict:
        """
        Get SMTP configuration from settings.
        
        Returns:
            Dictionary with SMTP configuration
            
        Raises:
            ValueError: If required SMTP settings are missing
        """
        if not self.settings.email_smtp_host:
            raise ValueError("SMTP host not configured. Set EMAIL_SMTP_HOST environment variable.")
        
        if not self.settings.email_smtp_username:
            raise ValueError("SMTP username not configured. Set EMAIL_SMTP_USERNAME environment variable.")
        
        if not self.settings.email_smtp_password:
            raise ValueError("SMTP password not configured. Set EMAIL_SMTP_PASSWORD environment variable.")
        
        if not self.settings.email_from_address:
            raise ValueError("From address not configured. Set EMAIL_FROM_ADDRESS environment variable.")
        
        return {
            "hostname": self.settings.email_smtp_host,
            "port": self.settings.email_smtp_port,
            "username": self.settings.email_smtp_username,
            "password": self.settings.email_smtp_password,
            "use_tls": self.settings.email_use_tls,
            "from_address": self.settings.email_from_address,
            "from_name": self.settings.email_from_name
        }
    
    def _render_template(
        self,
        template_name: str,
        report: Report,
        user_email: str
    ) -> Tuple[str, str]:
        """
        Render email template with report data.
        
        Args:
            template_name: Name of the template file
            report: Report model instance
            user_email: Recipient email address
            
        Returns:
            Tuple of (subject, html_body)
            
        Raises:
            TemplateNotFound: If template file doesn't exist
        """
        try:
            template = self.jinja_env.get_template(template_name)
        except TemplateNotFound:
            logger.warning(f"Template {template_name} not found, using default template")
            # Fallback to simple HTML from report_content
            subject = f"Competitive Intelligence Report - {report.report_type.title()}"
            html_body = report.report_content if report.report_content else "<p>No report content available.</p>"
            return subject, html_body
        
        # Prepare template context
        user_name = user_email.split("@")[0] if user_email else "there"
        context = {
            "report": report,
            "user_email": user_email,
            "user_name": user_name,
            "report_type_label": "🚨 EMERGENCY REPORT" if report.report_type == "emergency" else "📊 SCHEDULED REPORT",
            "generated_at": report.generated_at,
            "changes_detected": report.changes_detected,
            "critical_changes": report.critical_changes,
            "changes": report.changes,
            "insights": report.insights,
            "dashboard_url": "http://localhost:5173/",  # Adjust if a public URL is available
            "subtitle": report.metadata.get("subtitle") if getattr(report, "metadata", None) else None,
        }
        
        # Render template
        html_body = template.render(**context)
        
        # Generate subject (prefer LLM-provided)
        subject = None
        if getattr(report, "metadata", None):
            subject = report.metadata.get("email_subject")
        if not subject:
            if report.report_type == "emergency":
                subject = f"🚨 URGENT: {report.critical_changes} Critical Change(s) Detected"
            else:
                if report.changes_detected == 0:
                    subject = "📊 Market Intelligence Update: No Changes Detected"
                else:
                    subject = f"📊 Market Intelligence Update - {report.changes_detected} Change(s)"
        
        return subject, html_body
    
    def _validate_email(self, email: str) -> None:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Raises:
            ValueError: If email format is invalid
        """
        try:
            validate_email_address(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address format: {email}") from e
    
    @resilient(
        retry={"max_attempts": 3, "initial_delay": 1.0},
        circuit_breaker=True,
        error_handling=True
    )
    async def send_report_email(
        self,
        report: Report,
        user_email: str
    ) -> bool:
        """
        Send report email to user.
        
        Uses @resilient decorator for retry, circuit breaker, and error handling.
        
        Args:
            report: Report model instance to send
            user_email: Recipient email address
            
        Returns:
            True if email sent successfully, False otherwise
            
        Raises:
            ValueError: If SMTP configuration is invalid or email format is invalid
            Exception: If email sending fails (after retries)
        """
        try:
            # Validate email address
            self._validate_email(user_email)
            
            # Get SMTP configuration
            smtp_config = self._get_smtp_config()
            
            # Render email template
            subject, html_body = self._render_template(
                "report_email.html",
                report,
                user_email
            )
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["From"] = f"{smtp_config['from_name']} <{smtp_config['from_address']}>"
            message["To"] = user_email
            message["Subject"] = subject
            
            # Add HTML body
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Send email via SMTP
            logger.info(f"Sending email to {user_email} for report {report.report_id}")
            
            # For Gmail: port 587 uses STARTTLS; port 465 uses implicit TLS
            use_tls = smtp_config["use_tls"] and smtp_config["port"] == 465
            start_tls = smtp_config["use_tls"] and smtp_config["port"] == 587

            async with aiosmtplib.SMTP(
                hostname=smtp_config["hostname"],
                port=smtp_config["port"],
                use_tls=use_tls,
                start_tls=start_tls
            ) as smtp:
                await smtp.login(
                    smtp_config["username"],
                    smtp_config["password"]
                )
                await smtp.send_message(message)
            
            logger.info(f"Email sent successfully to {user_email} for report {report.report_id}")
            
            # Update report status in repository
            if self.report_repository:
                try:
                    await self.report_repository.mark_email_sent(report.report_id)
                    logger.info(f"Report {report.report_id} marked as email sent")
                except Exception as e:
                    logger.error(f"Failed to mark email as sent for report {report.report_id}: {e}")
                    # Don't fail the whole operation if repository update fails
            
            return True
            
        except ValueError as e:
            logger.error(f"Email configuration error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to send email to {user_email} for report {report.report_id}: {e}")
            raise
    
    async def send_test_email(self, to_email: str) -> bool:
        """
        Send a test email to verify SMTP configuration.
        
        Args:
            to_email: Recipient email address
            
        Returns:
            True if test email sent successfully
            
        Raises:
            ValueError: If SMTP configuration is invalid or email format is invalid
            Exception: If email sending fails
        """
        try:
            # Validate email address
            self._validate_email(to_email)
            
            smtp_config = self._get_smtp_config()

            use_tls = smtp_config["use_tls"] and smtp_config["port"] == 465
            start_tls = smtp_config["use_tls"] and smtp_config["port"] == 587

            message = MIMEMultipart("alternative")
            message["From"] = f"{smtp_config['from_name']} <{smtp_config['from_address']}>"
            message["To"] = to_email
            message["Subject"] = "Test Email - Market Intelligence Hub"
            
            html_body = """
            <html>
            <body>
                <h1>Test Email</h1>
                <p>This is a test email from Market Intelligence Hub.</p>
                <p>If you received this, your email configuration is working correctly.</p>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            async with aiosmtplib.SMTP(
                hostname=smtp_config["hostname"],
                port=smtp_config["port"],
                use_tls=use_tls,
                start_tls=start_tls
            ) as smtp:
                await smtp.login(
                    smtp_config["username"],
                    smtp_config["password"]
                )
                await smtp.send_message(message)
            
            logger.info(f"Test email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test email to {to_email}: {e}")
            raise
    
    @resilient(
        error_handling=True,
        retry={"max_attempts": 3, "initial_delay": 2.0, "exponential_base": 2.0},
        circuit_breaker={"failure_threshold": 5, "timeout": 60.0},
        rate_limiter={"tokens_per_second": 2.0}
    )
    async def send_emergency_email(
        self,
        user_id: str,
        recipient_email: str,
        changes: List[Dict[str, Any]],
        max_severity: float,
        recipient_name: Optional[str] = None
    ) -> bool:
        """
        Send emergency alert email for critical changes.
        
        This is sent immediately when critical thresholds are exceeded during scanning.
        
        Args:
            user_id: User identifier
            recipient_email: Email address of recipient
            changes: List of critical changes (severity >= threshold)
            max_severity: Maximum severity score detected
            recipient_name: Optional recipient name
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Validate email address
            self._validate_email(recipient_email)
            
            smtp_config = self._get_smtp_config()
            
            # Create email message
            message = MIMEMultipart("alternative")
            message["From"] = f"{smtp_config['from_name']} <{smtp_config['from_address']}>"
            message["To"] = recipient_email
            message["Subject"] = f"CRITICAL ALERT: {len(changes)} Critical Changes Detected"
            
            # Prepare emergency email content
            alert_level = "CRITICAL" if max_severity >= 0.9 else "HIGH"
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            
            # Build HTML body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .alert-box {{ background-color: #fee; border-left: 4px solid #c00; padding: 15px; margin: 20px 0; }}
                    .alert-critical {{ border-color: #c00; background-color: #fee; }}
                    .alert-high {{ border-color: #f60; background-color: #ffe; }}
                    .severity {{ font-size: 24px; font-weight: bold; color: #c00; }}
                    .change-item {{ background-color: #f9f9f9; border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 4px; }}
                    .change-type {{ font-weight: bold; color: #555; }}
                    .change-desc {{ margin-top: 5px; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="alert-box alert-{'critical' if max_severity >= 0.9 else 'high'}">
                        <h2>{alert_level} ALERT</h2>
                        <p><strong>Time:</strong> {timestamp}</p>
                        <p><strong>Severity:</strong> <span class="severity">{max_severity:.2f}</span></p>
                    </div>
                    
                    <p>Critical changes have been detected in your monitored competitors.</p>
                    <p><strong>{len(changes)} critical change(s)</strong> exceed your configured threshold.</p>
                    
                    <h3>Critical Changes:</h3>
            """
            
            # Add each critical change
            for i, change in enumerate(changes[:5], 1):  # Limit to 5 changes in emergency email
                change_type = change.get("change_type", "unknown").replace("_", " ").title()
                severity = change.get("severity", 0.0)
                description = change.get("description", "No description")
                url = change.get("url", "")
                
                html_body += f"""
                    <div class="change-item">
                        <div class="change-type">{i}. {change_type} (Severity: {severity:.2f})</div>
                        <div class="change-desc">{description}</div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">{url}</div>
                    </div>
                """
            
            if len(changes) > 5:
                html_body += f"""
                    <p style="font-style: italic; color: #666;">
                        ... and {len(changes) - 5} more critical change(s)
                    </p>
                """
            
            html_body += """
                    <p style="margin-top: 30px;">
                        <strong>Recommended Action:</strong> Review these changes immediately and 
                        assess their impact on your business strategy.
                    </p>
                    
                    <div class="footer">
                        <p>This is an automated emergency alert from Market Intelligence Hub.</p>
                        <p>You received this because critical changes exceeded your configured threshold.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Send email via SMTP
            async with aiosmtplib.SMTP(
                hostname=smtp_config["hostname"],
                port=smtp_config["port"],
                use_tls=smtp_config["use_tls"]
            ) as smtp:
                await smtp.login(
                    smtp_config["username"],
                    smtp_config["password"]
                )
                await smtp.send_message(message)
            
            logger.info(f"Emergency email sent to {recipient_email} (severity: {max_severity})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send emergency email to {recipient_email}: {e}")
            return False

    @resilient(
        error_handling=True,
        retry={"max_attempts": 3, "initial_delay": 2.0},
        circuit_breaker={"failure_threshold": 5, "timeout": 60.0}
    )
    async def send_scan_summary_email(
        self,
        recipient_email: str,
        scan_id: str,
        urls_scanned: int,
        change_count: int,
        changes: List[Dict[str, Any]],
        max_severity: float,
        execution_time: str
    ) -> bool:
        """
        Send a summary email after a manual scan completes using the standard template.
        """
        try:
            self._validate_email(recipient_email)
            smtp_config = self._get_smtp_config()
            
            # Create a Mock Report object to satisfy the template
            # Using a simple class to mimic Report model attributes
            class MockReport:
                def __init__(self):
                    self.report_id = scan_id
                    self.report_type = "manual_scan"
                    self.generated_at = datetime.utcnow()
                    self.changes_detected = change_count
                    self.critical_changes = len([c for c in changes if c.get("severity", 0) >= 0.8])
                    self.changes = changes
                    self.insights = []
                    self.metadata = {"email_subject": f"Manual Scan Results: {change_count} Changes Detected" if change_count > 0 else "Market Update: No Changes Detected – Strategic Pause"}
                    
                    # By leaving report_content empty, the template will render the default "Strategic Pause / No Changes" section
                    # exactly as defined in report_email.html lines 176-203.
                    self.report_content = None 
                    
                    # If changes exist, we should populate content so the template shows them.
                    # Since the template uses {{ report.report_content | safe }}, we need to generate HTML ONLY if changes exist.
                    if change_count > 0:
                        self.report_content = self._build_change_list_html(changes, urls_scanned, execution_time)

                def _build_change_list_html(self, changes, urls_scanned, execution_time):
                    # Only generate HTML if there ARE changes.
                    content = f"""
                    <div class="section">
                        <h3>Scan Summary</h3>
                        <ul class="list">
                            <li><strong>URLs Scanned:</strong> {urls_scanned}</li>
                            <li><strong>Execution Time:</strong> {execution_time}</li>
                        </ul>
                    </div>
                    
                    <div class="section">
                        <h3>Detailed Changes</h3>
                    """
                    for i, change in enumerate(changes[:10], 1):
                        c_type = change.get("change_type", "Change").replace("_", " ").title()
                        url = change.get("url", "Unknown URL")
                        desc = change.get("description", "No description available.")
                        severity = change.get("severity", 0)
                        color = "#ef4444" if severity >= 0.8 else "#f59e0b"
                        
                        content += f"""
                        <div style="background: #ffffff; border-left: 4px solid {color}; padding: 12px; margin-bottom: 12px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="font-weight:700; color:#1f2937;">{i}. {c_type} <span style="font-size:11px; color:#6b7280;">({severity:.2f})</span></div>
                            <div style="font-size:12px; color:#4b5563; margin-top:4px;">{url}</div>
                            <div style="margin-top:6px; color:#374151;">{desc}</div>
                        </div>
                        """
                    content += '</div>'
                    return content

            # Instantiate mock report
            mock_report = MockReport()
            
            # Render template using existing method
            # We bypass the normal subject generation in _render_template by mocking metadata
            subject, html_body = self._render_template(
                "report_email.html",
                mock_report,
                recipient_email
            )
            
            # Override subject for clarity
            subject = f"Manual Scan Completed: {change_count} Changes Detected"
            
            # Construct Message
            message = MIMEMultipart("alternative")
            message["From"] = f"{smtp_config['from_name']} <{smtp_config['from_address']}>"
            message["To"] = recipient_email
            message["Subject"] = subject
            
            # Attach HTML
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Send via SMTP (Reusing common logic would be better but this is safe/isolated)
            use_tls = smtp_config["use_tls"] and smtp_config["port"] == 465
            start_tls = smtp_config["use_tls"] and smtp_config["port"] == 587
            
            async with aiosmtplib.SMTP(
                hostname=smtp_config["hostname"],
                port=smtp_config["port"],
                use_tls=use_tls,
                start_tls=start_tls
            ) as smtp:
                await smtp.login(smtp_config["username"], smtp_config["password"])
                await smtp.send_message(message)
                
            logger.info(f"Manual scan summary sent to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send scan summary email: {e}")
            return False
