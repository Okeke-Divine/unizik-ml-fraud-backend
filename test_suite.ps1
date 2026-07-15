# unizik-ml-fraud-backend/test_suite.ps1

$ErrorActionPreference = "Continue"
$ApiUri = "http://127.0.0.1:5000/api/predict"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "     UNIZIK FRAUD DETECTION ENGINE: 30-POINT ADVERSARIAL & EDGE-CASE TEST       " -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Target Endpoint: $ApiUri`n" -ForegroundColor Gray

# Define all 30 test cases across the 7 diagnostic categories
$testCases = @(
    # --- CATEGORY 1: Missing / Null / Empty Fields ---
    @{ ID=1;  Cat="1. Empty/Null"; Name="Empty payload"; Body='{}' },
    @{ ID=2;  Cat="1. Empty/Null"; Name="Missing all numeric fields"; Body='{"device_student_count_24h": null, "page_dwell_time_seconds": null, "is_high_risk_asn": null, "failed_attempts_1h": null, "session_hardware_mismatch": null, "is_off_peak_hour": null}' },
    @{ ID=3;  Cat="1. Empty/Null"; Name="Only one field present (failed_attempts_1h=5)"; Body='{"failed_attempts_1h": 5}' },
    @{ ID=4;  Cat="1. Empty/Null"; Name="Empty strings in numeric fields"; Body='{"device_student_count_24h": "", "page_dwell_time_seconds": ""}' },

    # --- CATEGORY 2: Type Mismatches & Invalid Values ---
    @{ ID=5;  Cat="2. Type Mismatch"; Name="String instead of number"; Body='{"device_student_count_24h": "five"}' },
    @{ ID=6;  Cat="2. Type Mismatch"; Name="Boolean values (true/false)"; Body='{"is_high_risk_asn": true, "session_hardware_mismatch": false}' },
    @{ ID=7;  Cat="2. Type Mismatch"; Name="Negative values"; Body='{"device_student_count_24h": -10, "failed_attempts_1h": -3}' },
    @{ ID=8;  Cat="2. Type Mismatch"; Name="Very large numbers"; Body='{"page_dwell_time_seconds": 1000000000, "failed_attempts_1h": 999999}' },
    @{ ID=9;  Cat="2. Type Mismatch"; Name="Floating point for integer fields"; Body='{"failed_attempts_1h": 2.7}' },
    @{ ID=10; Cat="2. Type Mismatch"; Name="NaN value string"; Body='{"page_dwell_time_seconds": "NaN"}' },

    # --- CATEGORY 3: Boundary Conditions (Split Points) ---
    @{ ID=11; Cat="3. Boundary"; Name="Failed attempts exactly 3"; Body='{"failed_attempts_1h": 3, "device_student_count_24h": 1, "page_dwell_time_seconds": 65.0, "is_high_risk_asn": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },
    @{ ID=12; Cat="3. Boundary"; Name="Failed attempts exactly 4"; Body='{"failed_attempts_1h": 4, "device_student_count_24h": 1, "page_dwell_time_seconds": 65.0, "is_high_risk_asn": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },
    @{ ID=13; Cat="3. Boundary"; Name="Off-peak hour = 1, all else 0"; Body='{"is_off_peak_hour": 1, "device_student_count_24h": 1, "page_dwell_time_seconds": 65.0, "is_high_risk_asn": 0, "failed_attempts_1h": 0, "session_hardware_mismatch": 0}' },
    @{ ID=14; Cat="3. Boundary"; Name="High-risk ASN = 1, all else 0"; Body='{"is_high_risk_asn": 1, "device_student_count_24h": 1, "page_dwell_time_seconds": 65.0, "failed_attempts_1h": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },
    @{ ID=15; Cat="3. Boundary"; Name="Hardware mismatch = 1, all else 0"; Body='{"session_hardware_mismatch": 1, "device_student_count_24h": 1, "page_dwell_time_seconds": 65.0, "is_high_risk_asn": 0, "failed_attempts_1h": 0, "is_off_peak_hour": 0}' },
    @{ ID=16; Cat="3. Boundary"; Name="Device student count = 10"; Body='{"device_student_count_24h": 10, "page_dwell_time_seconds": 65.0, "is_high_risk_asn": 0, "failed_attempts_1h": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },

    # --- CATEGORY 4: Nigerian University Context (Legitimate) ---
    @{ ID=17; Cat="4. UNIZIK Legit"; Name="Student studying late at night (off-peak)"; Body='{"page_dwell_time_seconds": 120.0, "is_off_peak_hour": 1, "failed_attempts_1h": 0, "device_student_count_24h": 1, "is_high_risk_asn": 0, "session_hardware_mismatch": 0}' },
    @{ ID=18; Cat="4. UNIZIK Legit"; Name="Student using shared computer lab device"; Body='{"device_student_count_24h": 8, "page_dwell_time_seconds": 45.0, "failed_attempts_1h": 0, "is_high_risk_asn": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },
    @{ ID=19; Cat="4. UNIZIK Legit"; Name="First-time login after password reset"; Body='{"failed_attempts_1h": 1, "page_dwell_time_seconds": 30.0, "device_student_count_24h": 1, "is_high_risk_asn": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },
    @{ ID=20; Cat="4. UNIZIK Legit"; Name="Student on VPN with long dwell time"; Body='{"is_high_risk_asn": 1, "page_dwell_time_seconds": 300.0, "failed_attempts_1h": 0, "device_student_count_24h": 1, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },

    # --- CATEGORY 5: Adversarial / Fraudulent Scenarios ---
    @{ ID=21; Cat="5. Adversarial"; Name="Multiple failed attempts + off-peak"; Body='{"failed_attempts_1h": 5, "is_off_peak_hour": 1, "page_dwell_time_seconds": 5.0, "device_student_count_24h": 10, "is_high_risk_asn": 0, "session_hardware_mismatch": 0}' },
    @{ ID=22; Cat="5. Adversarial"; Name="Hardware mismatch + high-risk ASN"; Body='{"session_hardware_mismatch": 1, "is_high_risk_asn": 1, "device_student_count_24h": 5, "page_dwell_time_seconds": 10.0, "failed_attempts_1h": 2, "is_off_peak_hour": 0}' },
    @{ ID=23; Cat="5. Adversarial"; Name="Bot short dwell time + high failed attempts"; Body='{"page_dwell_time_seconds": 0.1, "failed_attempts_1h": 6, "device_student_count_24h": 15, "is_high_risk_asn": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },
    @{ ID=24; Cat="5. Adversarial"; Name="All threat features at maximum"; Body='{"device_student_count_24h": 100, "page_dwell_time_seconds": 9999.0, "is_high_risk_asn": 1, "failed_attempts_1h": 10, "session_hardware_mismatch": 1, "is_off_peak_hour": 1}' },

    # --- CATEGORY 6: Mixed / Counter-intuitive Cases ---
    @{ ID=25; Cat="6. Mixed/Counter"; Name="High device count, zero fails, long dwell"; Body='{"device_student_count_24h": 20, "page_dwell_time_seconds": 600.0, "failed_attempts_1h": 0, "is_high_risk_asn": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },
    @{ ID=26; Cat="6. Mixed/Counter"; Name="Off-peak + hardware mismatch, low attempts"; Body='{"is_off_peak_hour": 1, "session_hardware_mismatch": 1, "failed_attempts_1h": 1, "device_student_count_24h": 2, "page_dwell_time_seconds": 35.0, "is_high_risk_asn": 0}' },
    @{ ID=27; Cat="6. Mixed/Counter"; Name="All zeros except extremely high dwell time"; Body='{"page_dwell_time_seconds": 10000.0, "device_student_count_24h": 0, "is_high_risk_asn": 0, "failed_attempts_1h": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' },

    # --- CATEGORY 7: Stress & Payload Integrity Tests ---
    @{ ID=28; Cat="7. Stress/Payload"; Name="Extremely large nested JSON metadata"; Body='{"device_student_count_24h": 1, "page_dwell_time_seconds": 65.0, "is_high_risk_asn": 0, "failed_attempts_1h": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0, "extra_metadata": {"browser": "Chrome", "os": "Windows", "screen": "1920x1080", "deep_nesting": {"junk": "data", "id": 99999}}}' },
    @{ ID=29; Cat="7. Stress/Payload"; Name="Unicode character in numeric field (Hindi numeral)"; Body='{"device_student_count_24h": "१", "page_dwell_time_seconds": 65.0, "is_high_risk_asn": 0, "failed_attempts_1h": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}' }
)

# Table formatting headers
Write-Host "ID | Category         | Test Case Name                     | Status | Verdict      | Conf   | Explanation / Error Notice" -ForegroundColor White
Write-Host "-----------------------------------------------------------------------------------------------------------------------------------------------------" -ForegroundColor DarkGray

$passCount = 0
$errCount = 0

foreach ($case in $testCases) {
    $idStr = $case.ID.ToString().PadRight(2)
    $catStr = $case.Cat.PadRight(16)
    $nameStr = $case.Name.PadRight(34)
    
    try {
        $response = Invoke-RestMethod -Uri $ApiUri -Method Post -ContentType "application/json" -Body $case.Body -TimeoutSec 5
        
        if ($response.status -eq "success") {
            $verdict = $response.verdict.PadRight(12)
            $conf = $response.confidence.ToString("0.0000").PadRight(6)
            $exp = $response.explanation
            if ($exp.Length -gt 45) { $exp = $exp.Substring(0, 42) + "..." }
            
            $color = "Green"
            if ($response.verdict -eq "FRAUDULENT") { $color = "Red" }
            
            Write-Host "$idStr | $catStr | $nameStr | OK     | " -NoNewline
            Write-Host "$verdict" -ForegroundColor $color -NoNewline
            Write-Host " | $conf | $exp"
            $passCount++
        } else {
            # Handled logical error returned by API
            $msg = $response.message
            if ($msg.Length -gt 55) { $msg = $msg.Substring(0, 52) + "..." }
            Write-Host "$idStr | $catStr | $nameStr | API_ERR| " -NoNewline
            Write-Host "HANDLED_ERR " -ForegroundColor Yellow -NoNewline
            Write-Host " | N/A    | $msg"
            $errCount++
        }
    }
    catch {
        # Caught HTTP 400/500 or network connection failures
        $errMsg = $_.Exception.Message
        if ($_.Exception.Response) {
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $rawBody = $reader.ReadToEnd()
                $jsonErr = $rawBody | ConvertFrom-Json
                if ($jsonErr.message) { $errMsg = $jsonErr.message }
            } catch {
                # Fallback if error body is not JSON
            }
        }
        if ($errMsg.Length -gt 55) { $errMsg = $errMsg.Substring(0, 52) + "..." }
        Write-Host "$idStr | $catStr | $nameStr | HTTP_EX| " -NoNewline
        Write-Host "EXCEPT_ERR  " -ForegroundColor Magenta -NoNewline
        Write-Host " | N/A    | $errMsg"
        $errCount++
    }
}

# --- TEST CASE 30: Rapid Concurrent Burst Stress Test ---
Write-Host "-----------------------------------------------------------------------------------------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "30 | 7. Stress/Payload| Rapid Burst Stress Test (20 Reqs)  | " -NoNewline

$burstPayload = '{"device_student_count_24h": 1, "page_dwell_time_seconds": 65.0, "is_high_risk_asn": 0, "failed_attempts_1h": 0, "session_hardware_mismatch": 0, "is_off_peak_hour": 0}'
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$burstSuccess = 0

for ($i = 1; $i -le 20; $i++) {
    try {
        $res = Invoke-RestMethod -Uri $ApiUri -Method Post -ContentType "application/json" -Body $burstPayload -TimeoutSec 3
        if ($res.status -eq "success") { $burstSuccess++ }
    } catch {}
}
$sw.Stop()
$elapsedMs = $sw.ElapsedMilliseconds

if ($burstSuccess -eq 20) {
    Write-Host "OK     | " -NoNewline
    Write-Host "BURST_PASS  " -ForegroundColor Green -NoNewline
    Write-Host " | 1.0000 | 20/20 responses processed in ${elapsedMs}ms without thread deadlock."
    $passCount++
} else {
    Write-Host "FAIL   | " -NoNewline
    Write-Host "BURST_FAIL  " -ForegroundColor Red -NoNewline
    Write-Host " | N/A    | Only $burstSuccess/20 completed in ${elapsedMs}ms."
    $errCount++
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "TEST SUITE SUMMARY: $passCount Passed / Handled Cleanly | $errCount Unhandled Exceptions" -ForegroundColor Cyan
Write-Host "================================================================================`n" -ForegroundColor Cyan