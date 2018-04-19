#coding:utf-8
import math

class Stack(object): #在统计all_words时用到辅助栈
    # 初始化栈为空列表
    def __init__(self):
        self.items = []

    # 判断栈是否为空，返回布尔值
    def is_empty(self):
        return self.items == []

    # 返回栈顶元素
    def peek(self):
        return self.items[len(self.items) - 1]

    # 返回栈的大小
    def size(self):
        return len(self.items)

    # 入栈
    def push(self, item):
        self.items.append(item)

    # 出栈
    def pop(self):
        return self.items.pop()

def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
        return True
    else:
        return False

def is_number(uchar):
    """判断一个unicode是否是数字，注意训练集和测试集中的数字写法和普通的不太一样，用一个or并列考虑"""
    if uchar >= u'\u0030' and uchar <= u'\u0039' or (uchar >= '０' and uchar <= '９'):
        return True
    else:
        return False

def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar <= u'\u005a') or (uchar >= u'\u0061' and uchar <= u'\u007a'):
        return True
    else:
        return False

def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    if not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar)):
        return True
    else:
        return False

def get_corpus():
    #对训练集进行处理，得到语料库corpus
    f = open('corpus_for_ass2train.txt')
    corpus = []
    #将分好词的corpus_for_ass2train.txt中每个词读进words中
    for line in f.readlines():
        wordlist = line.split()
        corpus.extend(wordlist)

    for i in range(0, len(corpus)):
        #将corpus中的标点符号进行处理
        if  is_other(corpus[i]) == True:
            #如果当前字符为标点符号，将其改为S.多个标点符号的情况下只保留一个S
            if i!=0 and corpus[i-1] == 'S':
                corpus[i] = '#'
            else:
                corpus[i] = 'S'

    new_corpus = []
    for i in range(0,len(corpus)):
        if corpus[i] != '#':
            new_corpus.append(corpus[i])

    return new_corpus

def get_dic(n=2):
    #根据corpus构建二层字典，用于n_gram计算概率
    word_dic = {};count = 0 #count统计所有bigram的个数，用于拉普拉斯平滑
    for i in range(len(corpus)):
        if corpus[i] not in word_dic:
            word_dic[corpus[i]] = {}
        word_dic[corpus[i]][corpus[i]] = 1 + word_dic[corpus[i]].get(corpus[i], 0) #word独立出现的次数
        if i != len(corpus)-1:
            #统计该词和其后一个词出现的频数
            word_dic[corpus[i]][corpus[i+1]] = 1 + word_dic[corpus[i]].get(corpus[i+1], 0)

    for key in word_dic.keys():
        count += len(word_dic[key].keys()) - 1 #统计所有bigram的总数

    return word_dic, count

def get_all_words(sen, max_length = 5):
    #找到一个句子中所有可能被切分出来的词和其对应的起始位置和结束位置，max_length为前向匹配的最大长度
    all_words = []
    wordStack = Stack()
    for i in range(len(sen)):
        #将所有可能的切分结果以[word,i,j]的形式保存，其中i代表word开始的位置，j代表word结束的位置
        #这里借助栈的先进先出，使得更长匹配放在all_words结果的前面，可以明显改善最终结果和加快运算
        wordStack.push([sen[i],i,i])
        for j in range(1,max_length + 1):
            if i+j < len(sen):
                if sen[i:i+j+1] in corpus:
                    wordStack.push([sen[i:i+j+1],i,i+j])
        while(wordStack.size()!=0):
            all_words.append(wordStack.pop())
    return all_words

def seg_sentence(sen, max_length=5):
    #根据n_gram概率得到sen所有可能的切分结果
    all_words = get_all_words(sen) #先得到句子中所有可能被切分出的词
    seg_result = [] #保存所有可能的切分结果
    i = 0;flag = 0
    while(i < len(all_words)):
        word = all_words[i] #word是当前需要进行继续拼接的词
        if word[1] == 0 and word[2] != len(sen) - 1:  #还没有组成整个词序
            j = word[2] + 1 #word结束的地方
            if j <= len(sen)-1: #判断是否越界
                for word_later in all_words: #在所有的词中找到可以接在该word后面的词
                    if word_later[1] == j:
                        #拼接出一个新词，并计算概率
                        word_new = word[0] + ' ' + word_later[0]
                        max_p = max_prob(word_new)
                        #在所有词中进行搜索，看有没有和该新词对应位置一致的词，如果有，比较他们俩的概率，并除去概率小的，以减小大量无用计算
                        for word_old in all_words:
                            if word_old[1] == word[1] and word_old[2] == word_later[2] and word_old[0]!= word_new:
                                if max_prob(word_old[0]) >= max_p:
                                    #不添加新词
                                    max_p = max_prob(word_old[0])
                                else:
                                    all_words.remove(word_old)
                            #不满足搜索条件的时候直接break，加快运算
                            if word_old[1] > word[1]:
                                break
                        if max_p == max_prob(word_new) and [word_new, word[1], word_later[2]] not in all_words:
                            all_words.insert(flag,[word_new, word[1], word_later[2]])
                    elif word_later[1] > j:
                        break
                all_words.remove(word) #word的结果已经遍历完，可以从list中删除，避免后面无用计算
                i = flag

        #当找到一个满足条件的切分结果时，将其加到最终结果中，并把flag+1
        elif word[1] == 0 and word[2] == len(sen) - 1:
            if word[0] not in seg_result:
                seg_result.append(word[0])
            flag += 1
            i = flag;

        elif word[1] != 0:
            break

    return seg_result

def max_prob(seg_sen, n=2):
    #传入一个已经切分好的结果，利用n_gram计算该种切分结果下的概率，采用拉普拉斯平滑
    prob = 0
    #先将传入的切分后的结果按空格分开
    word_list = seg_sen.split(' ')
    word_list.insert(0,'S') #增加一个句首
    #计算的是条件概率，则计算在第i-1个词出现的情况下第i个词出现的概率
    for i in range(1,len(word_list)):
        if word_list[i-1] in word_dic:
            c1 = word_dic[word_list[i-1]][word_list[i-1]]
        else:c1 = 0
        if c1 == 0:
            c2 = 0
        else:
            c2 = word_dic[word_list[i-1]].get(word_list[i], 0)
        #第i个词的条件概率，取对数
        p = math.log((c2 + 0.1)/(c1 + bigram*0.1))
        prob += p
    return prob

def my_seg(sen, max_length = 5, n = 2):
    seg_result = seg_sentence(sen)
    best_prob = float('-Inf')
    best_seg = ''
    #比较所有的切分结果，取最大概率的分法
    for seg_sen in seg_result:
        prob = max_prob(seg_sen)
        if prob > best_prob:
            best_prob = prob
            best_seg = seg_sen
    return best_seg

def sentence_split(s):
    #遍历句子，对句子按汉字、数字、字母、标点符号切开，汉字还要进行MP断句
    result = []
    pre = ''
    word = ''
    number = ''
    alpha = ''
    for c in s:
        if is_other(c):
            #当前字符为标点符号时，将之前的结果保存
            if is_number(pre):
                result.append(number)
                number = ''
            elif is_alphabet(pre):
                result.append(alpha)
                alpha = ''
            elif is_chinese(pre):
                word = my_seg(word)
                result.append(word)
                word = ''
            result.append(c)
        elif is_number(c):
            #当前字符为数字时，累积保存
            number += c
            #之前的字符如果不是数字，进行保存
            if is_alphabet(pre):
                result.append(alpha)
                alpha = ''
            elif is_chinese(pre):
                word = my_seg(word)
                result.append(word)
                word = ''
        elif is_alphabet(c):
            #当前字符为字母时，累积保存
            alpha += c
            #之前的字符如果不是字母，进行保存
            if is_number(pre):
                result.append(number)
                number = ''
            elif is_chinese(pre):
                word = my_seg(word)
                result.append(word)
                word = ''
        else:
            word += c
            if is_number(pre):
                result.append(number)
                number = ''
            elif is_alphabet(pre):
                result.append(alpha)
                alpha = ''
        pre = c
    #将句子的最后部分保存
    if number != '':
        result.append(number)
    elif alpha != '':
        result.append(alpha)
    elif word != '':
        word = my_seg(word)
        result.append(word)
    return result

if __name__ == "__main__":
    global corpus, word_dic, bigram  #将这三个变量设为全局变量，避免重复传参
    corpus = get_corpus()
    word_dic, bigram = get_dic(corpus)
    f = open('corpus_for_ass2test.txt','r') #读入测试集
    fw = open('26.txt', 'w') #写入文件
    for line in f.readlines():
        sentence = sentence_split(line)
        str = ' '.join(sentence)
        print(str)
        fw.write(str)
    fw.close()
