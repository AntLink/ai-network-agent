package executor

import "regexp"

var (
	ciscoVersionRE = regexp.MustCompile(`Cisco IOS Software.*Version\s+([^,\s]+)`)
	ciscoUptimeRE  = regexp.MustCompile(`(?m)^\s*([^\r\n]+) uptime is (.+)$`)
	ciscoImageRE   = regexp.MustCompile(`System image file is "([^"]+)"`)
)

// NormalizeCiscoFacts maps the fixed IOS show-version response to the
// cross-language facts contract. Raw output remains available for diagnostics.
func NormalizeCiscoFacts(raw string) map[string]interface{} {
	result := map[string]interface{}{"vendor": "cisco", "platform": "ios"}
	if match := ciscoVersionRE.FindStringSubmatch(raw); len(match) == 2 {
		result["version"] = match[1]
	}
	if match := ciscoUptimeRE.FindStringSubmatch(raw); len(match) == 3 {
		result["hostname"] = match[1]
		result["uptime"] = match[2]
	}
	if match := ciscoImageRE.FindStringSubmatch(raw); len(match) == 2 {
		result["image_file"] = match[1]
	}
	return result
}
