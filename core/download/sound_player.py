# -*- coding: utf-8 -*-
"""声音提示模块"""

import os
import subprocess
import threading

from core.infrastructure.logger import log
from core.infrastructure.platform_utils import get_available_sound_players, get_platform


class _ProcessReaper:
    """异步回收通过 Popen 启动的播放器进程，避免产生僵尸进程。"""

    _processes = []
    _lock = threading.Lock()

    @classmethod
    def watch(cls, process: subprocess.Popen) -> None:
        """监控一个 Popen 进程并在退出后回收。"""
        with cls._lock:
            cls._processes.append(process)

        def _wait_and_remove():
            try:
                process.wait(timeout=60)
            except Exception:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    pass
            with cls._lock:
                if process in cls._processes:
                    cls._processes.remove(process)

        threading.Thread(target=_wait_and_remove, daemon=True).start()


class SoundPlayer:
    """跨平台声音播放器"""

    @staticmethod
    def _get_success_mp3_path():
        """获取项目内置成功音效文件的绝对路径"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, "resources", "mp3", "success.mp3")

    @staticmethod
    def play_completion_sound():
        """播放下载完成提示音。"""
        try:
            custom_sound = SoundPlayer._load_custom_sound_path()
            if custom_sound:
                SoundPlayer.play_custom_sound(custom_sound)
                log("INFO", "已播放下载完成提示音（自定义音效）")
                return

            success_mp3 = SoundPlayer._get_success_mp3_path()
            if os.path.exists(success_mp3):
                SoundPlayer._play_audio_file(success_mp3)
                log("INFO", "已播放下载完成提示音（内置音效）")
                return

            SoundPlayer._play_system_sound()
            log("INFO", "已播放下载完成提示音")
        except Exception as e:
            log("ERROR", f"播放提示音失败: {e}")

    @staticmethod
    def _load_custom_sound_path():
        """从设置中读取用户自定义音效路径。"""
        try:
            from core.config.settings_manager import get_settings_manager
            custom_sound = get_settings_manager().get("notification_custom_sound", "")
            if custom_sound and os.path.exists(custom_sound):
                return custom_sound
        except Exception:
            pass
        return None

    @staticmethod
    def _play_audio_file(audio_path):
        """使用平台可用播放器播放指定音频文件。"""
        system = get_platform()
        if system == "windows":
            SoundPlayer._play_windows_audio(audio_path)
            return

        players = get_available_sound_players()
        if not players:
            SoundPlayer._play_system_sound()
            return

        player = players[0]
        if player == "ffplay":
            process = subprocess.Popen(
                [player, "-nodisp", "-autoexit", audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif player == "mpv":
            process = subprocess.Popen(
                [player, "--no-video", audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            process = subprocess.Popen(
                [player, audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        _ProcessReaper.watch(process)

    @staticmethod
    def _play_windows_audio(audio_path):
        """Windows 系统播放音频文件。"""
        try:
            ext = os.path.splitext(audio_path)[1].lower()
            if ext == ".wav":
                import winsound
                winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            SoundPlayer._play_with_mci(audio_path)
        except Exception as e:
            log("WARNING", f"Windows 音频播放失败，回退系统提示音: {e}")
            try:
                SoundPlayer._play_system_sound()
            except Exception:
                pass

    @staticmethod
    def _play_with_mci(audio_path):
        """使用 Windows MCI 播放音频。"""
        try:
            import ctypes
            import uuid
            import time

            winmm = ctypes.windll.winmm
            mci_send = winmm.mciSendStringW
            alias = f"sed_sound_{uuid.uuid4().hex[:8]}"
            safe_path = audio_path.replace('"', '\\"')

            open_cmd = f'open "{safe_path}" type mpegvideo alias {alias}'
            ret = mci_send(open_cmd, None, 0, None)
            if ret != 0:
                open_cmd = f'open "{safe_path}" alias {alias}'
                ret = mci_send(open_cmd, None, 0, None)
                if ret != 0:
                    log("ERROR", f"MCI 打开音频失败，错误码: {ret}")
                    return False

            ret = mci_send(f'play {alias}', None, 0, None)
            if ret != 0:
                log("ERROR", f"MCI 播放音频失败，错误码: {ret}")
                mci_send(f'close {alias}', None, 0, None)
                return False

            def _close_after_play():
                try:
                    time.sleep(10)
                    mci_send(f'close {alias}', None, 0, None)
                except Exception:
                    pass

            threading.Thread(target=_close_after_play, daemon=True).start()
            return True
        except Exception as e:
            log("ERROR", f"MCI 播放异常: {e}")
            return False

    @staticmethod
    def _play_system_sound():
        """播放系统默认提示音。"""
        system = get_platform()
        if system == "windows":
            SoundPlayer._play_windows_beep()
        elif system == "darwin":
            SoundPlayer._play_mac_sound()
        else:
            SoundPlayer._play_linux_sound()

    @staticmethod
    def _play_windows_beep():
        """Windows 系统播放提示音。"""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            SoundPlayer._play_terminal_beep()

    @staticmethod
    def _play_mac_sound():
        """macOS 系统播放提示音。"""
        candidates = [
            SoundPlayer._get_success_mp3_path(),
            "/System/Library/Sounds/Glass.aiff",
        ]
        for path in candidates:
            if path and os.path.exists(path):
                SoundPlayer._play_audio_file(path)
                return
        SoundPlayer._play_terminal_beep()

    @staticmethod
    def _play_linux_sound():
        """Linux 系统播放提示音。"""
        success_mp3 = SoundPlayer._get_success_mp3_path()
        if success_mp3 and os.path.exists(success_mp3):
            SoundPlayer._play_audio_file(success_mp3)
            return
        candidates = [
            "/usr/share/sounds/freedesktop/stereo/complete.oga",
            "/usr/share/sounds/deepin/stereo/message.ogg",
            "/usr/share/sounds/gnome/default/alerts/glass.ogg",
        ]
        for path in candidates:
            if os.path.exists(path):
                SoundPlayer._play_audio_file(path)
                return
        SoundPlayer._play_terminal_beep()

    @staticmethod
    def _play_terminal_beep():
        """播放终端蜂鸣声（最后备用方案）。"""
        try:
            import sys
            sys.stdout.write("\a")
            sys.stdout.flush()
        except Exception:
            pass
        log("WARNING", "系统不支持声音播放")

    @staticmethod
    def play_custom_sound(sound_file_path):
        """播放自定义声音文件。"""
        if not sound_file_path or not os.path.exists(sound_file_path):
            log("WARNING", f"声音文件不存在: {sound_file_path}")
            SoundPlayer.play_completion_sound()
            return

        try:
            SoundPlayer._play_audio_file(sound_file_path)
            log("INFO", f"已播放自定义声音: {sound_file_path}")
        except Exception as e:
            log("ERROR", f"播放自定义声音失败: {e}")
            SoundPlayer.play_completion_sound()
