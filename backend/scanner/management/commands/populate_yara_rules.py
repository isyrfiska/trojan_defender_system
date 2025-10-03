from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from scanner.models import YaraRule

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate default YARA rules for malware detection'

    def handle(self, *args, **options):
        # Get or create a system user for default rules
        system_user, created = User.objects.get_or_create(
            email='system@trojandefender.local',
            defaults={
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        default_rules = [
            {
                'name': 'Generic_Trojan_Strings',
                'description': 'Detects common trojan-related strings',
                'rule_content': '''
rule Generic_Trojan_Strings
{
    meta:
        description = "Detects common trojan-related strings"
        author = "Trojan Defender"
        date = "2024-01-01"
        
    strings:
        $s1 = "backdoor" nocase
        $s2 = "keylogger" nocase
        $s3 = "password stealer" nocase
        $s4 = "remote access" nocase
        $s5 = "trojan" nocase
        $s6 = "malware" nocase
        
    condition:
        any of ($s*)
}
'''
            },
            {
                'name': 'Suspicious_Network_Activity',
                'description': 'Detects suspicious network-related strings',
                'rule_content': '''
rule Suspicious_Network_Activity
{
    meta:
        description = "Detects suspicious network activity patterns"
        author = "Trojan Defender"
        date = "2024-01-01"
        
    strings:
        $n1 = "socket" nocase
        $n2 = "connect" nocase
        $n3 = "send" nocase
        $n4 = "recv" nocase
        $n5 = "bind" nocase
        $n6 = "listen" nocase
        $url1 = /https?:\/\/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/
        
    condition:
        3 of ($n*) and $url1
}
'''
            },
            {
                'name': 'Registry_Manipulation',
                'description': 'Detects Windows registry manipulation',
                'rule_content': '''
rule Registry_Manipulation
{
    meta:
        description = "Detects Windows registry manipulation"
        author = "Trojan Defender"
        date = "2024-01-01"
        
    strings:
        $r1 = "RegOpenKey" nocase
        $r2 = "RegSetValue" nocase
        $r3 = "RegCreateKey" nocase
        $r4 = "RegDeleteKey" nocase
        $r5 = "HKEY_LOCAL_MACHINE" nocase
        $r6 = "HKEY_CURRENT_USER" nocase
        $r7 = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" nocase
        
    condition:
        2 of ($r1, $r2, $r3, $r4) and any of ($r5, $r6) and $r7
}
'''
            },
            {
                'name': 'File_System_Manipulation',
                'description': 'Detects suspicious file system operations',
                'rule_content': '''
rule File_System_Manipulation
{
    meta:
        description = "Detects suspicious file system operations"
        author = "Trojan Defender"
        date = "2024-01-01"
        
    strings:
        $f1 = "CreateFile" nocase
        $f2 = "WriteFile" nocase
        $f3 = "DeleteFile" nocase
        $f4 = "MoveFile" nocase
        $f5 = "CopyFile" nocase
        $temp = "\\temp\\" nocase
        $system = "\\system32\\" nocase
        $startup = "\\startup\\" nocase
        
    condition:
        3 of ($f*) and any of ($temp, $system, $startup)
}
'''
            },
            {
                'name': 'Process_Injection',
                'description': 'Detects process injection techniques',
                'rule_content': '''
rule Process_Injection
{
    meta:
        description = "Detects process injection techniques"
        author = "Trojan Defender"
        date = "2024-01-01"
        
    strings:
        $p1 = "VirtualAllocEx" nocase
        $p2 = "WriteProcessMemory" nocase
        $p3 = "CreateRemoteThread" nocase
        $p4 = "OpenProcess" nocase
        $p5 = "SetWindowsHookEx" nocase
        $p6 = "NtCreateThreadEx" nocase
        
    condition:
        2 of them
}
'''
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for rule_data in default_rules:
            rule, created = YaraRule.objects.get_or_create(
                name=rule_data['name'],
                defaults={
                    'description': rule_data['description'],
                    'rule_content': rule_data['rule_content'],
                    'created_by': system_user,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created YARA rule: {rule.name}')
                )
            else:
                # Update existing rule if content is different
                if rule.rule_content != rule_data['rule_content']:
                    rule.rule_content = rule_data['rule_content']
                    rule.description = rule_data['description']
                    rule.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated YARA rule: {rule.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'YARA rule already exists: {rule.name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new rules, updated {updated_count} existing rules.'
            )
        )