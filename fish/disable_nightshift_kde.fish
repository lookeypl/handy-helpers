#!/usr/bin/env fish

function disable_nightshift_kde -d "Disables Night Shift filter in KDE"
    if is_nightshift_enabled_kde
        qdbus org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut "Toggle Night Color"
    end
end
