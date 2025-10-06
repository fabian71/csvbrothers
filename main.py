import xbot
import xbot_visual
from . import package
from .package import variables as glv
import time
from xbot import print

def main(args):
    try:
        pastaImagens = xbot_visual.programing.variable(value="E:\\trampo\\vender nas microsstock\\artes___\\2025\\setembro\\30_09_2025\\image_to_vector"
        , _block=("main", 1, "Set variable"))
        remove_fundo = xbot_visual.programing.variable(value=False
        , _block=("main", 2, "Set variable"))
        arquivoControle = xbot_visual.programing.variable(value=xbot_visual.sh_str(pastaImagens) + "\\processados_automa.txt"
        , _block=("main", 3, "Set variable"))
        if xbot_visual.file.if_exist(path=arquivoControle, expect_exist="no_exist", _block=("main", 4, "If file exists")):
            xbot_visual.file.write(path=arquivoControle, content="  ", write_way="overwrite", is_text=True, new_line=False, encoding="UTF-8", _block=("main", 5, "Write to file"))
        #endif
        web_page = xbot_visual.web.create(web_type="chrome", value="https://pt.vectorizer.ai", silent_running=False, wait_load_completed=True, load_timeout="20", stop_load_if_load_timeout="handleExcept", chrome_file_name=None, edge_file_name=None, ie_file_name=None, bro360_file_name=None, firefox_file_name=None, arguments=None, _block=("main", 7, "Open webpage"))
        xbot_visual.win32.window.move(window_type="win_title_or_class", window="", selector=None, handle="", title="Conversão on-line de arquivos PNG e JPG para vetores SVG - Vectorizer.AI", handle_checked=False, class_name="", use_wildcard=False, x="20", y="20", _block=("main", 8, "Move window"))
        listaDeFicheiros = xbot_visual.dir.find_files(path=pastaImagens, patterns="*.jpeg*", find_subdir=False, skip_hidden_file=False, is_sort=False, sort_by="name", sort_way="increase", _block=("main", 9, "Get list of files in folder"))
        xbot_visual.dialog.show_notifycation(operation_kind="show", level="info", placement="top", message=arquivoControle, timeout="3", _block=("main", 10, "Display notification"))
        xbot_visual.programing.sleep(random_number=False, seconds="1", start_number="1", stop_number="5", _block=("main", 11, "Wait"))
        for loop_item in xbot_visual.workflow.list_iterator(list=listaDeFicheiros, loop_start_index="0", loop_end_index="-1", output_with_index=False, _block=("main", 12, "For each item in list")):
            conteudoArquivoControle = xbot_visual.file.read(path=arquivoControle, read_way="all_text", encoding="UTF-8", _block=("main", 13, "Read file"))
            if xbot_visual.workflow.test(operand1=conteudoArquivoControle, operator="not in", operand2=loop_item, operator_options="{\"ignoreCase\":\"False\"}", _block=("main", 14, "If")):
                xbot_visual.web.browser.navigate(browser=web_page, mode="url", url="https://pt.vectorizer.ai/", ignore_cache=False, load_timeout="20", _block=("main", 15, "Navigate to new URL"))
                xbot_visual.programing.sleep(random_number=False, seconds="1", start_number="1", stop_number="5", _block=("main", 16, "Wait"))
                xbot_visual.web.element.upload(browser=web_page, element=package.selector("selecionarPasta"), file_name=loop_item, simulate=False, clipboard_input=False, input_type="automatic", wait_dialog_appear_timeout="20", force_ime_ENG=False, send_key_delay="50", focus_timeout="1000", _block=("main", 17, "Upload file(s)"))
                xbot_visual.programing.sleep(random_number=False, seconds="20", start_number="1", stop_number="5", _block=("main", 18, "Wait"))
                if xbot_visual.workflow.test(operand1=remove_fundo, operator="is true", operand2="", operator_options="{}", _block=("main", 19, "If")):
                    xbot_visual.web.element.click(browser=web_page, element=package.selector("SeletorPaleta"), simulate=True, move_mouse=False, clicks="click", button="left", keys="null", delay_after="1", anchor_type="center", sudoku_part="MiddleCenter", offset_x="0", offset_y="0", timeout="20", _block=("main", 20, "Click Element (web)"))
                    xbot_visual.programing.sleep(random_number=False, seconds="8", start_number="1", stop_number="5", _block=("main", 21, "Wait"))
                    xbot_visual.win32.click_mouse(is_move_mouse_before_click=True, point_x="63", point_y="510", relative_to="screen", move_speed="middle", button="left", click_type="click", hardware_driver_click=False, keys="null", delay_after="1", _block=("main", 22, "Click mouse"))
                    xbot_visual.programing.sleep(random_number=False, seconds="1", start_number="1", stop_number="5", _block=("main", 23, "Wait"))
                    xbot_visual.web.element.click(browser=web_page, element=package.selector("Olho"), simulate=True, move_mouse=False, clicks="click", button="left", keys="null", delay_after="1", anchor_type="center", sudoku_part="MiddleCenter", offset_x="0", offset_y="0", timeout="20", _block=("main", 24, "Click Element (web)"))
                    xbot_visual.web.element.click(browser=web_page, element=package.selector("bt_v_azul"), simulate=True, move_mouse=False, clicks="click", button="left", keys="null", delay_after="1", anchor_type="center", sudoku_part="MiddleCenter", offset_x="0", offset_y="0", timeout="20", _block=("main", 25, "Click Element (web)"))
                    xbot_visual.programing.sleep(random_number=False, seconds="10", start_number="1", stop_number="5", _block=("main", 26, "Wait"))
                #endif
                xbot_visual.programing.sleep(random_number=False, seconds="5", start_number="1", stop_number="5", _block=("main", 28, "Wait"))
                xbot_visual.web.element.click(browser=web_page, element=package.selector("FAÇA DOWNLOAD_2"), simulate=True, move_mouse=False, clicks="click", button="left", keys="null", delay_after="1", anchor_type="center", sudoku_part="MiddleCenter", offset_x="0", offset_y="0", timeout="20", _block=("main", 29, "Click Element (web)"))
                xbot_visual.programing.sleep(random_number=False, seconds="8", start_number="1", stop_number="5", _block=("main", 30, "Wait"))
                # web.element.click
                # programing.sleep
                # web.element.click
                # programing.sleep
                xbot_visual.web.element.click(browser=web_page, element=package.selector("FAÇA DOWNLOAD_4"), simulate=True, move_mouse=False, clicks="click", button="left", keys="null", delay_after="2", anchor_type="center", sudoku_part="MiddleCenter", offset_x="0", offset_y="0", timeout="20", _block=("main", 35, "Click Element (web)"))
                # win32.click_mouse
                xbot_visual.programing.sleep(random_number=False, seconds="2", start_number="1", stop_number="5", _block=("main", 37, "Wait"))
                download_file_name = xbot_visual.web.handle_save_dialog(web_type="chrome", dialog_result="OK", file_folder=pastaImagens, use_custom_filename=False, file_name=None, wait_complete=False, wait_complete_timeout="", simulate=False, clipboard_input=False, input_type="automatic", wait_appear_timeout="20", force_ime_ENG=False, send_key_delay="50", focus_timeout="1000", _block=("main", 38, "Handle download dialog"))
                random_number = xbot_visual.programing.random_int(start_number="4", stop_number="9", _block=("main", 39, "Generate random number"))
                xbot_visual.file.write(path=arquivoControle, content=lambda: loop_item + '\n', write_way="append", is_text=True, new_line=False, encoding="UTF-8", _block=("main", 40, "Write to file"))
                xbot_visual.programing.sleep(random_number=False, seconds=random_number, start_number="1", stop_number="5", _block=("main", 41, "Wait"))
            #endif
        #endloop
    finally:
        pass
