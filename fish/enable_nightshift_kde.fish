#!/usr/bin/env fish

function enable_nightshift_kde -d "Enables Night Shift filter in KDE"
    if not is_nightshift_enabled_kde
        qdbus org.kde.kglobalaccel /component/kwin org.kde.kglobalaccel.Component.invokeShortcut "Toggle Night Color"
    end
end
