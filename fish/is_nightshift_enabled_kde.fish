#!/usr/bin/env fish

function is_nightshift_enabled_kde -d "Checks if Night Shift color filter is enabled on KDE"
    return (test "$(qdbus org.kde.KWin.NightLight /org/kde/KWin/NightLight org.kde.KWin.NightLight.running)" = "true")
end
