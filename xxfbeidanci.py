import tkinter as tk
from tkinter import messagebox, font
import pandas as pd
import random
import re
from pathlib import Path

class WordQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("不喜欢背任何东西！")
        self.root.geometry("900x700")  # 增大窗口尺寸
        self.root.resizable(True, True)
        
        # 设置整体背景色为灰色
        self.bg_color = "#f0f0f0"  # 浅灰色背景
        self.root.configure(bg=self.bg_color)
        
        # 数据变量
        self.word_bank = []
        self.all_chinese = []
        self.quiz_items = []
        self.current_index = 0
        self.score = 0
        self.total = 0
        self.current_options = []
        self.current_correct = ""
        self.answered = False
        self.is_correct = False
        self.auto_next_delay = 1000  # 答对后自动跳转延迟（毫秒），稍微放慢一点
        self.after_id = None
        
        # 加载单词库
        self.load_word_bank()
        
        # 创建界面
        self.create_widgets()
        
        # 如果单词库有效，开始测验
        if self.word_bank and len(self.word_bank) >= 4:
            self.start_quiz()
        else:
            self.show_no_words_message()
    
    def clean_chinese(self, text):
        """清理中文释义"""
        if pd.isna(text) or not isinstance(text, str):
            return None
        
        text = text.strip()
        if not text:
            return None
        
        # 移除括号内的内容
        text = re.sub(r'[（(][^）)]*[）)]', '', text)
        
        # 取第一个主要含义
        separators = ['，', ',', '；', ';', '、', '。']
        for sep in separators:
            if sep in text:
                text = text.split(sep)[0]
        
        text = text.strip()
        if len(text) > 20:  # 放宽长度限制
            text = text[:20] + "..."
        return text if text else None
    
    def load_word_bank(self):
        """从Excel加载单词库"""
        excel_file = "test.xlsx"
        
        if not Path(excel_file).exists():
            messagebox.showerror("错误", f"未找到文件: {excel_file}\n请确保文件在当前目录下")
            return
        
        try:
            df = pd.read_excel(excel_file, header=None)
            word_dict = {}
            
            for idx, row in df.iterrows():
                english = row[0] if pd.notna(row[0]) else None
                chinese_raw = row[1] if len(row) > 1 and pd.notna(row[1]) else None
                
                if not english or not chinese_raw:
                    continue
                
                english = str(english).strip().lower()
                if not english:
                    continue
                
                chinese = self.clean_chinese(chinese_raw)
                if not chinese:
                    continue
                
                if english not in word_dict:
                    word_dict[english] = chinese
            
            self.word_bank = [{'English': eng, 'Chinese': chi} for eng, chi in word_dict.items()]
            self.all_chinese = [item['Chinese'] for item in self.word_bank]
            
            print(f"成功加载 {len(self.word_bank)} 个单词")
            
            if len(self.word_bank) == 0:
                messagebox.showerror("错误", "没有找到有效的单词数据\n请确保Excel第一列是英文，第二列是中文")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载单词库失败: {e}\n请确保已安装openpyxl: pip install openpyxl")
    
    def create_widgets(self):
        """创建界面组件（使用大字体）"""
        # 顶部信息栏
        self.info_frame = tk.Frame(self.root, bg=self.bg_color)
        self.info_frame.pack(pady=15)
        
        self.score_label = tk.Label(
            self.info_frame, 
            text="得分: 0", 
            font=("微软雅黑", 16, "bold"),  # 增大字体
            bg=self.bg_color,
            fg="#2c3e50"
        )
        self.score_label.pack(side=tk.LEFT, padx=30)
        
        self.progress_label = tk.Label(
            self.info_frame, 
            text="进度: 0/0", 
            font=("微软雅黑", 16, "bold"),
            bg=self.bg_color,
            fg="#2c3e50"
        )
        self.progress_label.pack(side=tk.LEFT, padx=30)
        
        self.total_label = tk.Label(
            self.info_frame, 
            text=f"总词库: {len(self.word_bank)}", 
            font=("微软雅黑", 14),
            bg=self.bg_color,
            fg="#7f8c8d"
        )
        self.total_label.pack(side=tk.LEFT, padx=30)
        
        # 题目区域
        self.question_frame = tk.Frame(self.root, bg=self.bg_color)
        self.question_frame.pack(pady=40)
        
        self.question_label = tk.Label(
            self.question_frame, 
            text="", 
            font=("微软雅黑", 36, "bold"),  # 单词字体更大
            fg="#2c3e50", 
            bg=self.bg_color
        )
        self.question_label.pack()
        
        # 选项按钮区域
        self.options_frame = tk.Frame(self.root, bg=self.bg_color)
        self.options_frame.pack(pady=30)
        
        self.option_buttons = []
        for i in range(4):
            btn = tk.Button(
                self.options_frame, 
                text="", 
                font=("微软雅黑", 16),  # 选项字体增大
                width=30,
                height=2,
                bg="#ecf0f1",
                fg="#2c3e50",
                activebackground="#bdc3c7",
                cursor="hand2",  # 鼠标悬停时变成手型
                command=lambda idx=i: self.check_answer(idx)
            )
            btn.pack(pady=8)
            self.option_buttons.append(btn)
        
        # 反馈标签
        self.feedback_label = tk.Label(
            self.root, 
            text="", 
            font=("微软雅黑", 14),  # 反馈字体增大
            fg="blue", 
            bg=self.bg_color
        )
        self.feedback_label.pack(pady=15)
        
        # 下一题按钮（只在答错时显示）
        self.next_button = tk.Button(
            self.root, 
            text="下一题 →", 
            font=("微软雅黑", 14, "bold"),
            bg="#3498db",
            fg="navy",
            activebackground="#2980b9",
            cursor="hand2",
            command=self.manual_next_question,
            state=tk.DISABLED
        )
        # 先不pack，答错时才显示
        
        # 重新开始按钮
        self.restart_button = tk.Button(
            self.root,
            text="重新开始",
            font=("微软雅黑", 12),
            bg="#95a5a6",
            fg="navy",
            activebackground="#7f8c8d",
            cursor="hand2",
            command=self.restart_quiz
        )
        self.restart_button.pack(pady=8)
        
        # 添加提示标签
        self.hint_label = tk.Label(
            self.root,
            text="💡 提示：答对自动进入下一题，答错需手动点击\"下一题\"",
            font=("微软雅黑", 10),
            bg=self.bg_color,
            fg="#7f8c8d"
        )
        self.hint_label.pack(pady=5)
    
    def generate_distractors(self, correct_chinese, num_distractors=3):
        """生成干扰项"""
        pool = [c for c in self.all_chinese if c != correct_chinese]
        pool = list(set(pool))
        
        if len(pool) < num_distractors:
            defaults = ["美丽", "重要", "快速", "缓慢", "明亮", "黑暗", "高兴", "悲伤"]
            for d in defaults:
                if d not in pool and d != correct_chinese:
                    pool.append(d)
                if len(pool) >= num_distractors:
                    break
        
        return random.sample(pool, num_distractors)
    
    def start_quiz(self):
        """开始或重新开始测验"""
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        self.next_button.pack_forget()
        
        self.quiz_items = self.word_bank.copy()
        random.shuffle(self.quiz_items)
        
        self.current_index = 0
        self.score = 0
        self.total = len(self.quiz_items)
        self.answered = False
        
        self.update_score_display()
        self.update_progress_display()
        
        for btn in self.option_buttons:
            btn.config(state=tk.NORMAL, bg="#ecf0f1")
        
        self.feedback_label.config(text="")
        
        self.load_question()
    
    def load_question(self):
        """加载当前题目"""
        if self.current_index >= self.total:
            self.show_result()
            return
        
        self.answered = False
        self.is_correct = False
        
        self.next_button.pack_forget()
        
        item = self.quiz_items[self.current_index]
        english = item['English']
        correct = item['Chinese']
        self.current_correct = correct
        
        self.question_label.config(text=english.capitalize())
        
        distractors = self.generate_distractors(correct)
        self.current_options = distractors + [correct]
        random.shuffle(self.current_options)
        
        for i, btn in enumerate(self.option_buttons):
            btn.config(text=f"{chr(65+i)}. {self.current_options[i]}", bg="#ecf0f1", state=tk.NORMAL)
        
        self.feedback_label.config(text="")
    
    def check_answer(self, option_idx):
        """检查答案"""
        if self.answered:
            return
        
        self.answered = True
        selected = self.current_options[option_idx]
        is_correct = (selected == self.current_correct)
        
        for i, btn in enumerate(self.option_buttons):
            if self.current_options[i] == self.current_correct:
                btn.config(bg="#2ecc71")
            elif i == option_idx and not is_correct:
                btn.config(bg="#e74c3c")
        
        if is_correct:
            self.score += 1
            self.is_correct = True
            self.feedback_label.config(text=f"✓ 回答正确！「{self.current_correct}」", fg="green")
            self.update_score_display()
            
            for btn in self.option_buttons:
                btn.config(state=tk.DISABLED)
            
            self.after_id = self.root.after(self.auto_next_delay, self.auto_next_question)
        else:
            self.is_correct = False
            self.feedback_label.config(
                text=f"✗ 回答错误！正确答案是: {self.current_correct}", 
                fg="red"
            )
            
            for btn in self.option_buttons:
                btn.config(state=tk.DISABLED)
            
            self.next_button.pack(pady=15)
            self.next_button.config(state=tk.NORMAL)
    
    def auto_next_question(self):
        """答对后自动进入下一题"""
        self.after_id = None
        self.current_index += 1
        self.update_progress_display()
        
        if self.current_index < self.total:
            self.load_question()
        else:
            self.show_result()
    
    def manual_next_question(self):
        """答错后手动进入下一题"""
        self.next_button.pack_forget()
        self.next_button.config(state=tk.DISABLED)
        
        self.current_index += 1
        self.update_progress_display()
        
        if self.current_index < self.total:
            self.load_question()
        else:
            self.show_result()
    
    def update_score_display(self):
        self.score_label.config(text=f"得分: {self.score}")
    
    def update_progress_display(self):
        self.progress_label.config(text=f"进度: {self.current_index}/{self.total}")
    
    def show_result(self):
        percentage = (self.score / self.total * 100) if self.total > 0 else 0
        
        if self.score == self.total:
            comment = "🎉 太棒了！全对！继续努力！"
        elif self.score >= self.total * 0.8:
            comment = "👍 不错，继续保持！"
        elif self.score >= self.total * 0.6:
            comment = "📚 还可以，再复习一下会更棒！"
        else:
            comment = "💪 加油，多练习几次会更好！"
        
        result_text = f"测验完成！\n\n得分: {self.score}/{self.total} ({percentage:.1f}分)\n\n{comment}"
        
        if messagebox.askyesno("测验结果", result_text + "\n\n是否重新开始一轮测验？"):
            self.restart_quiz()
        else:
            for btn in self.option_buttons:
                btn.config(state=tk.DISABLED)
            self.question_label.config(text="测验结束")
            self.feedback_label.config(text="点击「重新开始」按钮开始新的一轮")
            self.next_button.pack_forget()
    
    def restart_quiz(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        self.next_button.pack_forget()
        
        random.shuffle(self.quiz_items)
        self.current_index = 0
        self.score = 0
        self.total = len(self.quiz_items)
        self.answered = False
        
        self.update_score_display()
        self.update_progress_display()
        self.feedback_label.config(text="")
        
        for btn in self.option_buttons:
            btn.config(state=tk.NORMAL, bg="#ecf0f1")
        
        self.load_question()
    
    def show_no_words_message(self):
        self.question_label.config(text="单词数量不足")
        self.feedback_label.config(
            text=f"当前词库只有 {len(self.word_bank)} 个有效单词\n需要至少4个单词才能开始测验", 
            fg="red"
        )
        for btn in self.option_buttons:
            btn.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = WordQuizApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
