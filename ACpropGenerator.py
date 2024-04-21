# =========================================================================
# ACpropGenerator.py
# ver.1.0.0 - 2024/04/21
# Author:Kotetsu
# 免責事項：本プログラムを使用したことで生じるあらゆる直接・間接的な損失等に対し
# 作者は何ら責任を負いません。
# =========================================================================


import xml.etree.ElementTree as ET
import flet as ft

# プロパティのXMLファイルを読込み辞書にする
def create_prop_dict(path):
    # XMLファイルを読み込む
    tree = ET.parse(path)
    root = tree.getroot()

    # グループ名とプロパティ名を組み合わせた文字列をキーとした辞書を生成する
    combined_dict = {}
    for group in root.findall(".//PropertyDefinitionGroup"):
        group_name = group.find("Name")
        if group_name is not None:
            group_name_text = group_name.text
            for prop in group.findall(".//PropertyDefinition"):
                prop_name = prop.find("Name")
                value_descriptor = prop.find("ValueDescriptor")
                if prop_name is not None and value_descriptor is not None:
                    descriptor_type = value_descriptor.get("Type")
                    # テキスト接続（/の前にエスケープシークエンス追加）
                    joined_text = group_name_text + "/" + prop_name.text.replace("/", "\\/")
                    # オプションセットかどうかの判定
                    if descriptor_type == "EnumerationValueDescriptor": # オプションセット
                        values_list = [value.text for value in value_descriptor.findall(".//Values/Value/Variant/Value")]
                        combined_dict[joined_text] = { # グループ名/プロパティ名
                            "ValueDescriptor": descriptor_type,
                            "ValueType": "", # 型
                            "isOptionSet":True, # オプションセットか？
                            "Options": values_list # オプションセットのリスト
                            }
                    # オプションセット以外    
                    elif descriptor_type == "SingleValueDescriptor":
                        ValueType = value_descriptor.find("ValueType")
                        combined_dict[joined_text] = {
                            "ValueDescriptor": descriptor_type,
                            "ValueType": ValueType.text,
                            "isOptionSet":False
                            }
    return combined_dict

# Flet
def main(page: ft.Page):
    page.scroll = "auto"
    page.window_min_width = 830
    page.window_width = 830
    # 入力のためのリスト定義
    arg_values = []
    return_values = []
    Operaters = []
    fields = []
    propsvalues = []

    # プロパティXML取得
    xml_file_path = 'props.xml'
    try:
        prop_dict = create_prop_dict(xml_file_path)
    except:
        page.snack_bar = ft.SnackBar(ft.Text("EROOR：props.xmlが見つかりません",color="Black"))
        page.snack_bar.open = True
        page.snack_bar.bgcolor = "Yellow"
        page.update()
        
    # 条件行追加処理
    def add_input(e,optionsetvalue:list):
        if props.value == None:
            page.snack_bar = ft.SnackBar(ft.Text("EROOR：先にプロパティを選択してください",color="Black"))
            page.snack_bar.open = True
            page.snack_bar.bgcolor = "Yellow"
        else:
            # 演算子ドロップダウン定義
            Operater = ft.Dropdown(
                label="演算子",
                options=[
                    ft.dropdown.Option("="),
                    ft.dropdown.Option("<>"),
                    ft.dropdown.Option("<"),
                    ft.dropdown.Option(">"),
                    ft.dropdown.Option("<="),
                    ft.dropdown.Option(">="),
                ],
                value = "=",
                width = 70
            )
            # 矢印テキスト定義
            yaji = ft.Text("▶")

            # 条件（プロパティがこれなら）テキスト or ドロップダウン定義
            arg_value = ft.TextField(label="こうなら")
            for propsvalue in propsvalues:
                # オプションセットじゃない場合 -> テキスト入力
                if prop_dict[propsvalue.value]["isOptionSet"] == False:
                    arg_value = ft.TextField(label="こうなら")
                # オプションセットの場合 -> ドロップダウン
                else:
                    arg_options = prop_dict[props.value]["Options"]
                    arg_value = ft.Dropdown(label="こうなら")
                    # オプションセットの内容をドロップダウンに追加
                    for arg_option in arg_options:
                        arg_value.options.append(ft.dropdown.Option(arg_option))
                    # オプションセット全追加した場合のデフォルト値処理
                    if optionsetvalue != None:
                        arg_value.value = optionsetvalue
            
            # 返り値テキスト定義
            return_value = ft.TextField(label="これ")

            # 他関数で使うためのリスト追加
            Operaters.append(Operater)
            arg_values.append(arg_value)
            return_values.append(return_value) 

            # 条件行削除ボタン定義
            delete_btn = ft.IconButton(
                ft.icons.REMOVE,
                tooltip="この条件行を削除",
                on_click=lambda e,
                tf=arg_value: remove_row(arg_value) # 削除処理へ
            )

            # 操作パネルの追加行定義
            row = ft.Row(
                [Operater, arg_value, yaji, return_value, delete_btn]
            )

            # 他関数で使うためのリスト追加
            fields.append(row)

            # 操作部分追加
            page.controls.insert(-2, row)
            # page.controls.append(row)

        page.update()

    # 条件行削除処理
    def remove_row(tf):
        i = 0
        # 削除する行を探す
        for row in fields:
            if tf in row.controls:
                # ページから行を削除
                page.controls.remove(row)
                # 各リストから行を削除
                fields.remove(row)  
                arg_values.remove(arg_values[i])
                return_values.remove(return_values[i])
                Operaters.remove(Operaters[i])
                break
            i = i + 1
        page.update()

    # Archicadコピペ用文字列作成処理
    def get_values(e,argtypeindex:int,returntypeindex:int,otherwiseTF:bool,otherwisetext:str):
        try:
            propname = "{Property:" + props.value + '} ' # {Property:<プロパティグループ/プロパティ名>} 
            output = "IFS ( " # コピペ用文字列

            # 条件行数分繰り返し
            for count in range(len(arg_values)):
                # + {Property:<プロパティグループ/プロパティ名>}<Operater>
                output = output + propname + Operaters[count].value
                # <こうなら>の型設定（ユーザー）が文字列/数値か
                if argtypeindex == 1: # 数値
                    valuetext = arg_values[count].value #<こうなら>
                else: # 文字列
                    valuetext = '"' + arg_values[count].value + '"' #"<こうなら>""
                # + {Property:<プロパティグループ/プロパティ名>}<Operater> ["]<こうなら>["],
                output = output + valuetext +', '
                # <これ>の型設定（ユーザー）が文字列/数値か
                if returntypeindex == 1: # 数値
                    valuetext = return_values[count].value #<これ>
                    otherwisetext2 = otherwisetext # <どの条件にも当てはまらない場合はこれ>
                else: # 文字列
                    valuetext = '"' + return_values[count].value + '"' #"<これ>""
                    otherwisetext2 = '"' + otherwisetext + '"' # "<どの条件にも当てはまらない場合はこれ>
                # + {Property:<プロパティグループ/プロパティ名>}<Operater> ["]<こうなら>["], ["]<これ>["]
                output = output + valuetext +', '
            
            # どの条件にも当てはまらないテキストの処理
            if otherwiseTF:
                output = output + "TRUE," + otherwisetext2
            else:
                output = output[:-len(", ")] # しない場合は最後のカンマを消す
            output = output + ")"

            # コピペ用の枠に表示
            output_text.value = output

            page.update()
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text("EROOR：プロパティが選択されていません。または「こうなら」に入力がありません。",color="Black"))
            page.snack_bar.open = True
            page.snack_bar.bgcolor = "Yellow"
            page.update()

    # 全削除処理
    def clear_all(e):
        # 全条件行削除
        for row in fields:
            page.controls.remove(row)
        # 全リストクリア
        fields.clear()
        arg_values.clear()
        return_values.clear()
        Operaters.clear()

        page.update()

    # プロパティ変更処理
    def do_value_update(e):
        # 全削除
        clear_all(None)

        # propsvaluesリストに選択したプロパティを書き込む
        propsvalues.clear()
        propsvalues.append(props)

        page.update()
    
    # 全オプションセットを書き込んだ行を追加処理
    def add_all_optionset(e):
        if props.value == None:
            page.snack_bar = ft.SnackBar(ft.Text("EROOR：先にプロパティを選択してください",color="Black"))
            page.snack_bar.open = True
            page.snack_bar.bgcolor = "Yellow"
        else:
            # ひとつしかないpropsvaluesから単体要素を取り出す
            for propsvalue in propsvalues:
                pass
            # オプションセット書き込み
            if prop_dict[propsvalue.value]["isOptionSet"] == True:
                arg_options = prop_dict[props.value]["Options"]
                for arg_option in arg_options:
                    add_input(None,arg_option) # 行追加する

            else:
                page.snack_bar = ft.SnackBar(ft.Text("EROOR：オプションセットではありません",color="Black"))
                page.snack_bar.open = True
                page.snack_bar.bgcolor = "Yellow"
        page.update()            



    ##########################################
    # Fletメイン処理
    ##########################################

    page.title = "数式エディタジェネレータ(IFS)"

    anot_text = ft.Text('※同じフォルダに"props.xml"という名前でプロパティマネージャから出力したXMLファイルを保存してください')



    # プロパティ指定
    ## ドロップダウン定義
    props = ft.Dropdown(label="このプロパティが",on_change=do_value_update)
    ## XMLから選択肢追加 
    for key , value in prop_dict.items():
        props.options.append(ft.dropdown.Option(key))

    # 条件行追加
    ## 追加ボタン定義
    add_btn = ft.IconButton(
        ft.icons.ADD,
        tooltip="条件行を追加",
        on_click=lambda e:add_input(
            e,
            None
        )
    )
    
    # コピペ文字列追加
    ## 登録ボタン定義
    get_btn = ft.IconButton(
        ft.icons.APP_REGISTRATION,
        tooltip="コピペ用文字列を生成",
        on_click=lambda e: get_values(
            e,
            argtype_btm.selected_index,
            returntype_btm.selected_index,
            otherwise_btn.value,
            otherwise_value.value
        )
    )

    # <こうなら>型指定
    ## 説明テキスト定義
    argtype_text = ft.Text("「こうなら」の値タイプ：")
    ## ボタン定義
    argtype_btm = ft.CupertinoSlidingSegmentedButton(
        selected_index=0,
        thumb_color=ft.colors.BLUE_400,
        #on_change=lambda e: print(f"selected_index: {e.data}"),
        padding=ft.padding.symmetric(0, 10),
        controls=[
            ft.Text("テキスト"),
            ft.Text("数値"),
        ],
    )

    # <これ>型指定
    ## 説明テキスト定義
    returntype_text = ft.Text("「これ」の値タイプ：")
    ## ボタン定義
    returntype_btm = ft.CupertinoSlidingSegmentedButton(
        selected_index=0,
        thumb_color=ft.colors.BLUE_400,
        #on_change=lambda e: print(f"selected_index: {e.data}"),
        padding=ft.padding.symmetric(0, 10),
        controls=[
            ft.Text("テキスト"),
            ft.Text("数値"),
        ],
    )

    # <どれにも当てはまらない>
    ## ボタン定義
    otherwise_btn = ft.CupertinoSwitch(
        label="どれにも当てはまらない ▶",
        value=False,
        tooltip="「どれにも当てはまらない場合」を設定する場合はON"
    )
    ## <これ>入力定義
    otherwise_value = ft.TextField(label="これ")

    # オプションセット選択肢全追加
    ## ボタン定義
    add_all_optionset_btn = ft.IconButton(ft.icons.DONE_ALL,tooltip="オプションセットを全追加",on_click=add_all_optionset)

    # 全条件行削除
    ## ボタン定義
    clear_all_btn = ft.IconButton(ft.icons.CLEAR, on_click=clear_all,tooltip="すべての条件行を削除")

    # コピペ用文字列
    ## テキストフィールド定義
    output_text = ft.TextField(label="ここにコピペ用文字列が出る",max_lines=5,expand=True)



    # ボタンをページに追加
    page.add(anot_text,props)
    page.controls.append(
        ft.Container(
            ft.Row(
                [add_btn,add_all_optionset_btn,clear_all_btn],
            ),
            padding=10,
            bgcolor=ft.colors.GREEN_50,
            border_radius=10,
            width=170,
        )      
    )
    page.add(
        ft.Container(
            ft.Row([argtype_text,argtype_btm,returntype_text,returntype_btm]),
            padding=10,
            bgcolor=ft.colors.GREEN_50,
            border_radius=10,
            width=600,
        )
    )
    page.controls.append(ft.Row([otherwise_btn,otherwise_value]))
    page.controls.append(
        ft.Container(
            ft.Row([get_btn,output_text]),
            padding=10,
            bgcolor=ft.colors.DEEP_ORANGE_50,
            border_radius=10,
        )
    )
    page.update()

ft.app(target=main)
