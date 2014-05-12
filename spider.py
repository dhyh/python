#coding:utf-8
import Queue,re,urllib2
import threading
#Beautiful Soup 是用 Python 写的一个 HTML/XML 的解析器，
#它可以很好的处理不规范标记并生成剖析树。
#from BeautifulSoup import BeautifulSoup

# 目标
task_url="http://www.baidu.com/"
# 结果队列
result_list={}
result_list.update({task_url:0})
spider_list=Queue.Queue(10)

class ThreadPool(object):
    def __init__(self, size):
        self._queue = Queue.Queue()
        #threading.Condition()
        #A factory function that returns a new condition variable object. 
        #A condition variable allows one or more threads to wait until they are notified by another thread.
        self._data_ready = threading.Condition()
        #threading.Event()
        #A factory function that returns a new event object. 
        #An event manages a flag that can be set to true with the set() method and reset to false with the clear() method. 
        #The wait() method blocks until the flag is true.
        self._exit_flag = threading.Event()
        self._threads = []
        for i in range(size):
            t = threading.Thread(target=self._run, name=str(i))
            t.start()
            self._threads.append(t) #加入列表

    def add_task(self, callback, *args):
        self._queue.put((callback, args))
        with self._data_ready:
            #The notify() method wakes up one of the threads waiting for the condition variable, 
            #if any are waiting. The notifyAll() method wakes up all threads waiting for the condition variable.
            self._data_ready.notify()

    def join(self):
        self._queue.join()
        self._exit_flag.set()
        with self._data_ready:
            self._data_ready.notify_all()
        for t in self._threads:
            t.join()

    def _run(self):
        while True:
            with self._data_ready:
                while self._queue.empty() and not self._exit_flag.is_set():
                    self._data_ready.wait()
                if self._exit_flag.is_set():
                    break
                cb, args = self._queue.get_nowait()
            cb(*args)
            self._queue.task_done()

def spr_url(url):
    try:
        body_text=urllib2.urlopen(url).read()
        soup=BeautifulSoup(body_text)
        links=soup.findAll('a')
        for link in links:
            _url=link.get('href').encode('utf-8')
            if re.match('^(javascript|:;|#|mailto)',_url) or _url is None or re.match('.(jpg|png|bmp|mp3|wma|wmv|gz|zip|rar|iso|pdf|txt|db)$',_url):
                continue
            if re.match('^(http|https)',_url):
                if not re.match('^'+url,_url):
                    continue
                else:
                    if result_list.has_key(_url):
                        continue
                    else:
                        rst=_url.encode('utf-8')
                        print "[*][!] 发现连接:"+rst
                        result_list.update({rst:0})
            else:
                if result_list.has_key(url+_url):
                    continue
                else:
                    rst=url+_url
                    print "[*][!] 发现新连接: "+rst.encode('utf-8')
                    result_list.update({rst.encode('utf-8'):0})
    except Exception,error:
        print 'Exception Error :', error

while True:
    # 查看目标有多少个待爬
    for url in result_list:
        if result_list[url] == 0:
            # 每次放入10个任务到任务池，控制数量
            if not spider_list.full():
                spider_list.put(url)

    # 判断队列是否还有任务，如果有则爬，没有则任务结束
    if spider_list.empty():
        print "Spider is Finish!"
        for r_item in result_list:
            print "-------- Sprider Results -----------"
            print "URl: " + r_item
            print "------------------------------------"
        break
    else:
        thr = ThreadPool(10)
        # 取出URL 并且爬虫，结果放入result_list
        for num in range(spider_list.qsize()):
            thr.add_task(spr_url, spider_list.get())
        thr.join()

