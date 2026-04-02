$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

function New-Color {
    param([int]$R, [int]$G, [int]$B)
    return [System.Drawing.Color]::FromArgb($R, $G, $B)
}

function Draw-RoundRect {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Pen]$Pen,
        [System.Drawing.Brush]$Brush,
        [int]$X,
        [int]$Y,
        [int]$Width,
        [int]$Height,
        [int]$Radius = 18
    )

    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $diameter = $Radius * 2
    $path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $path.AddArc($X + $Width - $diameter, $Y + $Height - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()

    if ($null -ne $Brush) {
        $Graphics.FillPath($Brush, $path)
    }
    if ($null -ne $Pen) {
        $Graphics.DrawPath($Pen, $path)
    }
    $path.Dispose()
}

function Draw-Text {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Text,
        [System.Drawing.Font]$Font,
        [System.Drawing.Brush]$Brush,
        [float]$X,
        [float]$Y
    )

    $Graphics.DrawString($Text, $Font, $Brush, $X, $Y)
}

function Draw-NavItem {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Label,
        [int]$Y,
        [bool]$Active = $false
    )

    $activeFill = New-Object System.Drawing.SolidBrush (New-Color 232 119 84)
    $inactiveFill = New-Object System.Drawing.SolidBrush (New-Color 246 237 231)
    $textBrush = New-Object System.Drawing.SolidBrush (New-Color 34 40 49)
    $font = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Regular)
    $fontActive = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)

    if ($Active) {
        Draw-RoundRect -Graphics $Graphics -Pen $null -Brush $activeFill -X 34 -Y $Y -Width 252 -Height 52 -Radius 18
        Draw-Text -Graphics $Graphics -Text $Label -Font $fontActive -Brush ([System.Drawing.Brushes]::White) -X 58 -Y ($Y + 11)
    } else {
        Draw-RoundRect -Graphics $Graphics -Pen $null -Brush $inactiveFill -X 34 -Y $Y -Width 252 -Height 52 -Radius 18
        Draw-Text -Graphics $Graphics -Text $Label -Font $font -Brush $textBrush -X 58 -Y ($Y + 11)
    }

    $activeFill.Dispose()
    $inactiveFill.Dispose()
    $textBrush.Dispose()
    $font.Dispose()
    $fontActive.Dispose()
}

function Draw-CardTitle {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Title,
        [string]$Subtitle,
        [int]$X,
        [int]$Y,
        [int]$Width,
        [int]$Height,
        [System.Drawing.Color]$FillColor
    )

    $fill = New-Object System.Drawing.SolidBrush $FillColor
    $titleBrush = New-Object System.Drawing.SolidBrush (New-Color 34 40 49)
    $subBrush = New-Object System.Drawing.SolidBrush (New-Color 104 112 122)
    $titleFont = New-Object System.Drawing.Font("Georgia", 18, [System.Drawing.FontStyle]::Bold)
    $subFont = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Regular)

    Draw-RoundRect -Graphics $Graphics -Pen $null -Brush $fill -X $X -Y $Y -Width $Width -Height $Height -Radius 24
    Draw-Text -Graphics $Graphics -Text $Title -Font $titleFont -Brush $titleBrush -X ($X + 22) -Y ($Y + 20)
    Draw-Text -Graphics $Graphics -Text $Subtitle -Font $subFont -Brush $subBrush -X ($X + 22) -Y ($Y + 58)

    $fill.Dispose()
    $titleBrush.Dispose()
    $subBrush.Dispose()
    $titleFont.Dispose()
    $subFont.Dispose()
}

function Draw-Button {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Label,
        [int]$X,
        [int]$Y,
        [int]$Width,
        [int]$Height,
        [System.Drawing.Color]$FillColor,
        [System.Drawing.Color]$TextColor
    )

    $fill = New-Object System.Drawing.SolidBrush $FillColor
    $textBrush = New-Object System.Drawing.SolidBrush $TextColor
    $font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)

    Draw-RoundRect -Graphics $Graphics -Pen $null -Brush $fill -X $X -Y $Y -Width $Width -Height $Height -Radius 18
    Draw-Text -Graphics $Graphics -Text $Label -Font $font -Brush $textBrush -X ($X + 18) -Y ($Y + 12)

    $fill.Dispose()
    $textBrush.Dispose()
    $font.Dispose()
}

function Draw-Input {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Label,
        [string]$Value,
        [int]$X,
        [int]$Y,
        [int]$Width,
        [int]$Height
    )

    $pen = New-Object System.Drawing.Pen (New-Color 214 206 198), 1
    $fill = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $labelBrush = New-Object System.Drawing.SolidBrush (New-Color 106 114 124)
    $valueBrush = New-Object System.Drawing.SolidBrush (New-Color 34 40 49)
    $labelFont = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)
    $valueFont = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Regular)

    Draw-Text -Graphics $Graphics -Text $Label -Font $labelFont -Brush $labelBrush -X $X -Y ($Y - 22)
    Draw-RoundRect -Graphics $Graphics -Pen $pen -Brush $fill -X $X -Y $Y -Width $Width -Height $Height -Radius 14
    Draw-Text -Graphics $Graphics -Text $Value -Font $valueFont -Brush $valueBrush -X ($X + 16) -Y ($Y + 13)

    $pen.Dispose()
    $fill.Dispose()
    $labelBrush.Dispose()
    $valueBrush.Dispose()
    $labelFont.Dispose()
    $valueFont.Dispose()
}

function Draw-Chip {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Text,
        [int]$X,
        [int]$Y,
        [int]$Width
    )

    $fill = New-Object System.Drawing.SolidBrush (New-Color 243 228 211)
    $textBrush = New-Object System.Drawing.SolidBrush (New-Color 97 67 42)
    $font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    Draw-RoundRect -Graphics $Graphics -Pen $null -Brush $fill -X $X -Y $Y -Width $Width -Height 34 -Radius 17
    Draw-Text -Graphics $Graphics -Text $Text -Font $font -Brush $textBrush -X ($X + 12) -Y ($Y + 8)
    $fill.Dispose()
    $textBrush.Dispose()
    $font.Dispose()
}

function Draw-SectionHeader {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$Title,
        [string]$Subtitle,
        [int]$X,
        [int]$Y
    )

    $titleFont = New-Object System.Drawing.Font("Georgia", 26, [System.Drawing.FontStyle]::Bold)
    $subFont = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Regular)
    $titleBrush = New-Object System.Drawing.SolidBrush (New-Color 34 40 49)
    $subBrush = New-Object System.Drawing.SolidBrush (New-Color 101 110 120)
    Draw-Text -Graphics $Graphics -Text $Title -Font $titleFont -Brush $titleBrush -X $X -Y $Y
    Draw-Text -Graphics $Graphics -Text $Subtitle -Font $subFont -Brush $subBrush -X $X -Y ($Y + 44)
    $titleFont.Dispose()
    $subFont.Dispose()
    $titleBrush.Dispose()
    $subBrush.Dispose()
}

function Draw-Table {
    param(
        [System.Drawing.Graphics]$Graphics,
        [int]$X,
        [int]$Y,
        [int]$Width,
        [int]$RowHeight,
        [string[]]$Headers,
        [object[][]]$Rows,
        [int[]]$ColumnWidths = @()
    )

    $panelFill = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $panelPen = New-Object System.Drawing.Pen (New-Color 225 219 212), 1
    $headerFill = New-Object System.Drawing.SolidBrush (New-Color 246 242 238)
    $textBrush = New-Object System.Drawing.SolidBrush (New-Color 49 54 63)
    $mutedBrush = New-Object System.Drawing.SolidBrush (New-Color 115 121 131)
    $font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Regular)
    $headerFont = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $dividerPen = New-Object System.Drawing.Pen (New-Color 236 231 226), 1

    $headerHeight = 44
    $totalHeight = $headerHeight + ($Rows.Count * $RowHeight)
    Draw-RoundRect -Graphics $Graphics -Pen $panelPen -Brush $panelFill -X $X -Y $Y -Width $Width -Height $totalHeight -Radius 22
    Draw-RoundRect -Graphics $Graphics -Pen $null -Brush $headerFill -X $X -Y $Y -Width $Width -Height $headerHeight -Radius 22

    if ($ColumnWidths.Count -eq 0) {
        $columnWidths = @(260, 170, 230, 210, 130)
    } else {
        $columnWidths = $ColumnWidths
    }
    $offset = $X + 18
    for ($i = 0; $i -lt $Headers.Length; $i++) {
        Draw-Text -Graphics $Graphics -Text $Headers[$i] -Font $headerFont -Brush $mutedBrush -X $offset -Y ($Y + 12)
        if ($i -lt ($Headers.Length - 1)) {
            $offset += $columnWidths[$i]
        }
    }

    for ($rowIndex = 0; $rowIndex -lt $Rows.Count; $rowIndex++) {
        $top = $Y + $headerHeight + ($rowIndex * $RowHeight)
        $colX = $X + 18
        for ($col = 0; $col -lt $Rows[$rowIndex].Length; $col++) {
            $brush = if ($col -eq ($Rows[$rowIndex].Length - 1)) { $mutedBrush } else { $textBrush }
            Draw-Text -Graphics $Graphics -Text ([string]$Rows[$rowIndex][$col]) -Font $font -Brush $brush -X $colX -Y ($top + 15)
            if ($col -lt ($Rows[$rowIndex].Length - 1)) {
                $colX += $columnWidths[$col]
            }
        }
        if ($rowIndex -lt ($Rows.Count - 1)) {
            $Graphics.DrawLine($dividerPen, $X + 18, $top + $RowHeight - 1, $X + $Width - 18, $top + $RowHeight - 1)
        }
    }

    $panelFill.Dispose()
    $panelPen.Dispose()
    $headerFill.Dispose()
    $textBrush.Dispose()
    $mutedBrush.Dispose()
    $font.Dispose()
    $headerFont.Dispose()
    $dividerPen.Dispose()
}

function New-Canvas {
    param(
        [string]$Path,
        [scriptblock]$Painter
    )

    $bitmap = New-Object System.Drawing.Bitmap 1600, 900
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
    $graphics.Clear((New-Color 245 239 233))

    & $Painter $graphics

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

function Draw-BaseChrome {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$ActiveNav
    )

    $sidebarFill = New-Object System.Drawing.SolidBrush (New-Color 252 248 244)
    $topFill = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $accentBrush = New-Object System.Drawing.SolidBrush (New-Color 232 119 84)
    $brandBrush = New-Object System.Drawing.SolidBrush (New-Color 36 44 54)
    $brandFont = New-Object System.Drawing.Font("Georgia", 24, [System.Drawing.FontStyle]::Bold)
    $smallFont = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)
    $smallBrush = New-Object System.Drawing.SolidBrush (New-Color 121 128 136)

    Draw-RoundRect -Graphics $Graphics -Pen $null -Brush $sidebarFill -X 20 -Y 20 -Width 290 -Height 860 -Radius 36
    Draw-RoundRect -Graphics $Graphics -Pen $null -Brush $topFill -X 330 -Y 20 -Width 1250 -Height 92 -Radius 28

    $Graphics.FillEllipse($accentBrush, 54, 48, 28, 28)
    Draw-Text -Graphics $Graphics -Text "Ludostock" -Font $brandFont -Brush $brandBrush -X 98 -Y 38
    Draw-Text -Graphics $Graphics -Text "Referentiel metier" -Font $smallFont -Brush $smallBrush -X 100 -Y 72

    Draw-NavItem -Graphics $Graphics -Label "Vue d'ensemble" -Y 150 -Active ($ActiveNav -eq "overview")
    Draw-NavItem -Graphics $Graphics -Label "Jeux" -Y 214 -Active ($ActiveNav -eq "games")
    Draw-NavItem -Graphics $Graphics -Label "Auteurs" -Y 278 -Active ($ActiveNav -eq "authors")
    Draw-NavItem -Graphics $Graphics -Label "Editeurs" -Y 342 -Active ($ActiveNav -eq "editors")
    Draw-NavItem -Graphics $Graphics -Label "Distributeurs" -Y 406 -Active ($ActiveNav -eq "distributors")

    Draw-Text -Graphics $Graphics -Text "CRUD visible cote backend" -Font $smallFont -Brush $smallBrush -X 362 -Y 52
    Draw-Text -Graphics $Graphics -Text "create / list / detail / delete" -Font $smallFont -Brush $smallBrush -X 362 -Y 72

    $sidebarFill.Dispose()
    $topFill.Dispose()
    $accentBrush.Dispose()
    $brandBrush.Dispose()
    $brandFont.Dispose()
    $smallFont.Dispose()
    $smallBrush.Dispose()
}

$outputDir = Split-Path -Parent $MyInvocation.MyCommand.Path

New-Canvas -Path (Join-Path $outputDir "mockup_referentiel_overview.png") -Painter {
    param($g)
    Draw-BaseChrome -Graphics $g -ActiveNav "overview"
    Draw-SectionHeader -Graphics $g -Title "Pilotage du referentiel" -Subtitle "Entree rapide par type d'entite, avec des actions volontairement simples." -X 360 -Y 140

    Draw-CardTitle -Graphics $g -Title "Jeux" -Subtitle "Creation riche avec rattachements multiples." -X 360 -Y 250 -Width 270 -Height 140 -FillColor (New-Color 250 225 216)
    Draw-CardTitle -Graphics $g -Title "Auteurs" -Subtitle "Liste simple, ajout rapide, suppression." -X 650 -Y 250 -Width 270 -Height 140 -FillColor (New-Color 229 239 230)
    Draw-CardTitle -Graphics $g -Title "Editeurs" -Subtitle "Meme logique que le CRUD backend." -X 940 -Y 250 -Width 270 -Height 140 -FillColor (New-Color 226 235 246)
    Draw-CardTitle -Graphics $g -Title "Distributeurs" -Subtitle "Gestion de noms et verification des doublons." -X 1230 -Y 250 -Width 270 -Height 140 -FillColor (New-Color 246 233 214)

    Draw-CardTitle -Graphics $g -Title "Workflow recommande" -Subtitle "1. Ouvrir une section  2. Ajouter ou consulter  3. Supprimer si besoin" -X 360 -Y 430 -Width 580 -Height 170 -FillColor (New-Color 255 255 255)
    Draw-CardTitle -Graphics $g -Title "Points UX lies au backend" -Subtitle "Pas d'update expose, donc pas de faux mode edition. Les erreurs 409 doivent etre visibles sur le champ Nom." -X 960 -Y 430 -Width 540 -Height 170 -FillColor (New-Color 255 255 255)

    Draw-CardTitle -Graphics $g -Title "Vue detail jeu" -Subtitle "Panneau lateral de consultation avec contributeurs relies." -X 360 -Y 630 -Width 360 -Height 170 -FillColor (New-Color 255 255 255)
    Draw-CardTitle -Graphics $g -Title "Listes referentielles" -Subtitle "Table compacte, recherche locale, ajout inline, confirmation de suppression." -X 740 -Y 630 -Width 360 -Height 170 -FillColor (New-Color 255 255 255)
    Draw-CardTitle -Graphics $g -Title "Extensible" -Subtitle "Le pattern auteur peut etre duplique plus tard pour artistes." -X 1120 -Y 630 -Width 380 -Height 170 -FillColor (New-Color 255 255 255)
}

New-Canvas -Path (Join-Path $outputDir "mockup_referentiel_games.png") -Painter {
    param($g)
    Draw-BaseChrome -Graphics $g -ActiveNav "games"
    Draw-SectionHeader -Graphics $g -Title "Gestion des jeux" -Subtitle "Ecran principal pour lister, consulter et creer un jeu selon le payload GameCreate." -X 360 -Y 140

    Draw-Input -Graphics $g -Label "Recherche locale" -Value "Catan" -X 360 -Y 248 -Width 300 -Height 48
    Draw-Input -Graphics $g -Label "Type" -Value "Jeu de base" -X 680 -Y 248 -Width 190 -Height 48
    Draw-Input -Graphics $g -Label "Annee" -Value "1995" -X 890 -Y 248 -Width 150 -Height 48
    Draw-Button -Graphics $g -Label "+ Nouveau jeu" -X 1280 -Y 244 -Width 170 -Height 54 -FillColor (New-Color 232 119 84) -TextColor ([System.Drawing.Color]::White)

    $rows = @(
        @("Catan", "Jeu de base", "Klaus Teuber", "Kosmos", "Voir  |  Supprimer"),
        @("7 Wonders Duel", "Jeu de base", "Bauza, Cathala", "Repos Prod", "Voir  |  Supprimer"),
        @("Carcassonne - Auberges", "Extension", "K. J. Wrede", "Hans im Gluck", "Voir  |  Supprimer"),
        @("Azul", "Jeu de base", "Michael Kiesling", "Plan B Games", "Voir  |  Supprimer")
    )
    Draw-Table -Graphics $g -X 360 -Y 330 -Width 890 -RowHeight 58 -Headers @("Nom", "Type", "Auteurs", "Editeur", "Actions") -Rows $rows -ColumnWidths @(230, 145, 195, 180, 110)

    $panelFill = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $panelPen = New-Object System.Drawing.Pen (New-Color 225 219 212), 1
    Draw-RoundRect -Graphics $g -Pen $panelPen -Brush $panelFill -X 1270 -Y 330 -Width 250 -Height 420 -Radius 24
    Draw-SectionHeader -Graphics $g -Title "Detail" -Subtitle "GET /api/games/{id}" -X 1290 -Y 352
    Draw-Input -Graphics $g -Label "Nom" -Value "Catan" -X 1290 -Y 450 -Width 210 -Height 44
    Draw-Input -Graphics $g -Label "Type" -Value "Jeu de base" -X 1290 -Y 530 -Width 210 -Height 44
    Draw-Text -Graphics $g -Text "Contributeurs" -Font (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)) -Brush (New-Object System.Drawing.SolidBrush (New-Color 106 114 124)) -X 1290 -Y 596
    Draw-Chip -Graphics $g -Text "Auteur: Klaus Teuber" -X 1290 -Y 620 -Width 170
    Draw-Chip -Graphics $g -Text "Editeur: Kosmos" -X 1290 -Y 662 -Width 150
    Draw-Chip -Graphics $g -Text "Distributeur: Asmodee" -X 1290 -Y 704 -Width 180
    Draw-Button -Graphics $g -Label "Supprimer" -X 1290 -Y 760 -Width 120 -Height 48 -FillColor (New-Color 74 84 97) -TextColor ([System.Drawing.Color]::White)
    Draw-Button -Graphics $g -Label "Fermer" -X 1420 -Y 760 -Width 80 -Height 48 -FillColor (New-Color 234 229 224) -TextColor (New-Color 52 58 67)
    $panelFill.Dispose()
    $panelPen.Dispose()
}

New-Canvas -Path (Join-Path $outputDir "mockup_referentiel_game_create.png") -Painter {
    param($g)
    Draw-BaseChrome -Graphics $g -ActiveNav "games"
    Draw-SectionHeader -Graphics $g -Title "Creation d'un jeu" -Subtitle "Formulaire simple en une page, strictement aligne sur GameCreate." -X 360 -Y 140

    $panelFill = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $panelPen = New-Object System.Drawing.Pen (New-Color 225 219 212), 1
    Draw-RoundRect -Graphics $g -Pen $panelPen -Brush $panelFill -X 360 -Y 230 -Width 1140 -Height 580 -Radius 30

    Draw-Input -Graphics $g -Label "Nom du jeu" -Value "Terraforming Mars" -X 400 -Y 300 -Width 420 -Height 48
    Draw-Input -Graphics $g -Label "Type" -Value "Jeu de base" -X 850 -Y 300 -Width 220 -Height 48
    Draw-Input -Graphics $g -Label "Extension de" -Value "Laisser vide si aucun" -X 1100 -Y 300 -Width 360 -Height 48

    Draw-Input -Graphics $g -Label "Annee" -Value "2016" -X 400 -Y 395 -Width 180 -Height 48
    Draw-Input -Graphics $g -Label "Joueurs min" -Value "1" -X 610 -Y 395 -Width 140 -Height 48
    Draw-Input -Graphics $g -Label "Joueurs max" -Value "5" -X 780 -Y 395 -Width 140 -Height 48
    Draw-Input -Graphics $g -Label "Age min" -Value "12" -X 950 -Y 395 -Width 140 -Height 48
    Draw-Input -Graphics $g -Label "Duree (min)" -Value "120" -X 1120 -Y 395 -Width 140 -Height 48

    Draw-Input -Graphics $g -Label "URL fiche" -Value "https://..." -X 400 -Y 490 -Width 520 -Height 48
    Draw-Input -Graphics $g -Label "URL image" -Value "https://..." -X 950 -Y 490 -Width 510 -Height 48

    Draw-Text -Graphics $g -Text "Auteurs" -Font (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)) -Brush (New-Object System.Drawing.SolidBrush (New-Color 106 114 124)) -X 400 -Y 580
    Draw-Chip -Graphics $g -Text "Jacob Fryxelius" -X 400 -Y 606 -Width 140
    Draw-Chip -Graphics $g -Text "+ ajouter" -X 550 -Y 606 -Width 100

    Draw-Text -Graphics $g -Text "Editeurs" -Font (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)) -Brush (New-Object System.Drawing.SolidBrush (New-Color 106 114 124)) -X 720 -Y 580
    Draw-Chip -Graphics $g -Text "FryxGames" -X 720 -Y 606 -Width 110
    Draw-Chip -Graphics $g -Text "Intrafin" -X 840 -Y 606 -Width 90
    Draw-Chip -Graphics $g -Text "+ ajouter" -X 940 -Y 606 -Width 100

    Draw-Text -Graphics $g -Text "Distributeurs" -Font (New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)) -Brush (New-Object System.Drawing.SolidBrush (New-Color 106 114 124)) -X 1100 -Y 580
    Draw-Chip -Graphics $g -Text "Asmodee" -X 1100 -Y 606 -Width 96
    Draw-Chip -Graphics $g -Text "+ ajouter" -X 1206 -Y 606 -Width 100

    Draw-CardTitle -Graphics $g -Title "Regle UX" -Subtitle "Si un nom n'existe pas dans le referentiel, le backend peut le creer au moment du POST /api/games/." -X 400 -Y 680 -Width 540 -Height 86 -FillColor (New-Color 250 245 239)
    Draw-CardTitle -Graphics $g -Title "Gestion d'erreur" -Subtitle "Afficher un message clair en cas de doublon dans une meme liste de contributeurs." -X 970 -Y 680 -Width 490 -Height 86 -FillColor (New-Color 250 245 239)

    Draw-Button -Graphics $g -Label "Annuler" -X 1240 -Y 744 -Width 100 -Height 48 -FillColor (New-Color 235 230 226) -TextColor (New-Color 54 60 69)
    Draw-Button -Graphics $g -Label "Creer le jeu" -X 1350 -Y 744 -Width 120 -Height 48 -FillColor (New-Color 232 119 84) -TextColor ([System.Drawing.Color]::White)

    $panelFill.Dispose()
    $panelPen.Dispose()
}

New-Canvas -Path (Join-Path $outputDir "mockup_referentiel_entities.png") -Painter {
    param($g)
    Draw-BaseChrome -Graphics $g -ActiveNav "authors"
    Draw-SectionHeader -Graphics $g -Title "Auteurs, editeurs, distributeurs" -Subtitle "Trois listes jumelles, chacune basee sur name + id avec creation et suppression." -X 360 -Y 140

    $panelFill = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
    $panelPen = New-Object System.Drawing.Pen (New-Color 225 219 212), 1

    Draw-RoundRect -Graphics $g -Pen $panelPen -Brush $panelFill -X 360 -Y 240 -Width 360 -Height 520 -Radius 24
    Draw-RoundRect -Graphics $g -Pen $panelPen -Brush $panelFill -X 750 -Y 240 -Width 360 -Height 520 -Radius 24
    Draw-RoundRect -Graphics $g -Pen $panelPen -Brush $panelFill -X 1140 -Y 240 -Width 360 -Height 520 -Radius 24

    Draw-SectionHeader -Graphics $g -Title "Auteurs" -Subtitle "POST / GET / DELETE" -X 385 -Y 266
    Draw-SectionHeader -Graphics $g -Title "Editeurs" -Subtitle "POST / GET / DELETE" -X 775 -Y 266
    Draw-SectionHeader -Graphics $g -Title "Distributeurs" -Subtitle "POST / GET / DELETE" -X 1165 -Y 266

    Draw-Input -Graphics $g -Label "Nouveau nom" -Value "Bruno Cathala" -X 385 -Y 360 -Width 240 -Height 46
    Draw-Button -Graphics $g -Label "Ajouter" -X 635 -Y 356 -Width 65 -Height 46 -FillColor (New-Color 232 119 84) -TextColor ([System.Drawing.Color]::White)

    Draw-Input -Graphics $g -Label "Nouveau nom" -Value "Repos Production" -X 775 -Y 360 -Width 240 -Height 46
    Draw-Button -Graphics $g -Label "Ajouter" -X 1025 -Y 356 -Width 65 -Height 46 -FillColor (New-Color 232 119 84) -TextColor ([System.Drawing.Color]::White)

    Draw-Input -Graphics $g -Label "Nouveau nom" -Value "Blackrock Games" -X 1165 -Y 360 -Width 240 -Height 46
    Draw-Button -Graphics $g -Label "Ajouter" -X 1415 -Y 356 -Width 65 -Height 46 -FillColor (New-Color 232 119 84) -TextColor ([System.Drawing.Color]::White)

    $authorRows = @(
        @("1", "Klaus Teuber", "Supprimer"),
        @("2", "Bruno Cathala", "Supprimer"),
        @("3", "Antoine Bauza", "Supprimer")
    )
    $editorRows = @(
        @("1", "Kosmos", "Supprimer"),
        @("2", "Repos Production", "Supprimer"),
        @("3", "Space Cowboys", "Supprimer")
    )
    $distRows = @(
        @("1", "Asmodee", "Supprimer"),
        @("2", "Blackrock Games", "Supprimer"),
        @("3", "Novalis", "Supprimer")
    )

    Draw-Table -Graphics $g -X 385 -Y 435 -Width 315 -RowHeight 56 -Headers @("ID", "Nom", "Action") -Rows $authorRows -ColumnWidths @(60, 150, 70)
    Draw-Table -Graphics $g -X 775 -Y 435 -Width 315 -RowHeight 56 -Headers @("ID", "Nom", "Action") -Rows $editorRows -ColumnWidths @(60, 150, 70)
    Draw-Table -Graphics $g -X 1165 -Y 435 -Width 315 -RowHeight 56 -Headers @("ID", "Nom", "Action") -Rows $distRows -ColumnWidths @(60, 150, 70)

    Draw-CardTitle -Graphics $g -Title "Feedback attendu" -Subtitle "Sur 409, afficher 'Ce nom existe deja' juste sous le champ." -X 360 -Y 790 -Width 530 -Height 76 -FillColor (New-Color 250 245 239)
    Draw-CardTitle -Graphics $g -Title "Comportement simple" -Subtitle "Pas d'edition inline tant que le backend n'expose pas d'update." -X 910 -Y 790 -Width 590 -Height 76 -FillColor (New-Color 250 245 239)

    $panelFill.Dispose()
    $panelPen.Dispose()
}

Write-Output "Mockups generated in $outputDir"
