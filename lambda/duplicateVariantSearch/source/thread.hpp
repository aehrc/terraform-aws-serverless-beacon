#pragma once

// Source: https://github.com/mvorbrodt/blog/blob/master/src/lesson_thread_pool_how_to.cpp
// Source: https://github.com/mvorbrodt/blog/blob/master/src/queue.hpp
// Author: https://vorbrodt.blog/2019/02/27/advanced-thread-pool/

#include <tuple>
#include <atomic>
#include <vector>
#include <thread>
#include <memory>
#include <future>
#include <utility>
#include <stdexcept>
#include <functional>
#include <type_traits>
#include <mutex>
#include <queue>
#include <condition_variable>

template<typename T>
class unbounded_queue
{
public:
	explicit unbounded_queue(bool block = true)
	: m_block{ block } {}

	void push(const T& item)
	{
		{
			std::scoped_lock guard(m_queue_lock);
			m_queue.push(item);
		}
		m_condition.notify_one();
	}

	void push(T&& item)
	{
		{
			std::scoped_lock guard(m_queue_lock);
			m_queue.push(std::move(item));
		}
		m_condition.notify_one();
	}

	template<typename... Args>
	void emplace(Args&&... args)
	{
		{
			std::scoped_lock guard(m_queue_lock);
			m_queue.emplace(std::forward<Args>(args)...);
		}
		m_condition.notify_one();
	}

	bool try_push(const T& item)
	{
		{
			std::unique_lock lock(m_queue_lock, std::try_to_lock);
			if(!lock)
				return false;
			m_queue.push(item);
		}
		m_condition.notify_one();
		return true;
	}

	bool try_push(T&& item)
	{
		{
			std::unique_lock lock(m_queue_lock, std::try_to_lock);
			if(!lock)
				return false;
			m_queue.push(std::move(item));
		}
		m_condition.notify_one();
		return true;
	}

	bool pop(T& item)
	{
		std::unique_lock guard(m_queue_lock);
		m_condition.wait(guard, [&]() { return !m_queue.empty() || !m_block; });
		if(m_queue.empty())
			return false;
		item = std::move(m_queue.front());
		m_queue.pop();
		return true;
	}

	bool try_pop(T& item)
	{
		std::unique_lock lock(m_queue_lock, std::try_to_lock);
		if(!lock || m_queue.empty())
			return false;
		item = std::move(m_queue.front());
		m_queue.pop();
		return true;
	}

	std::size_t size() const
	{
		std::scoped_lock guard(m_queue_lock);
		return m_queue.size();
	}

	bool empty() const
	{
		std::scoped_lock guard(m_queue_lock);
		return m_queue.empty();
	}

	void block()
	{
		std::scoped_lock guard(m_queue_lock);
		m_block = true;
	}

	void unblock()
	{
		{
			std::scoped_lock guard(m_queue_lock);
			m_block = false;
		}
		m_condition.notify_all();
	}

	bool blocking() const
	{
		std::scoped_lock guard(m_queue_lock);
		return m_block;
	}

private:
	using queue_t = std::queue<T>;
	queue_t m_queue;

	bool m_block;

	mutable std::mutex m_queue_lock;
	std::condition_variable m_condition;
};

class thread_pool
{
public:
	explicit thread_pool(std::size_t thread_count = std::thread::hardware_concurrency())
	: m_queues(thread_count), m_count(thread_count)
	{
		if(!thread_count)
			throw std::invalid_argument("bad thread count! must be non-zero!");

		auto worker = [this](auto i)
		{
			while(true)
			{
				proc_t f;
				for(std::size_t n = 0; n < m_count * K; ++n)
					if(m_queues[(i + n) % m_count].try_pop(f))
						break;
				if(!f && !m_queues[i].pop(f))
					break;
				f();
			}
		};

		m_threads.reserve(thread_count);
		for(std::size_t i = 0; i < thread_count; ++i)
			m_threads.emplace_back(worker, i);
	}

	~thread_pool()
	{
		for(auto& queue : m_queues)
			queue.unblock();
		for(auto& thread : m_threads)
			thread.join();
	}

	template<typename F, typename... Args>
	void enqueue_work(F&& f, Args&&... args)
	{
		auto work = [p = std::forward<F>(f), t = std::make_tuple(std::forward<Args>(args)...)]() { std::apply(p, t); };
		auto i = m_index++;

		for(std::size_t n = 0; n < m_count * K; ++n)
			if(m_queues[(i + n) % m_count].try_push(work))
				return;

		m_queues[i % m_count].push(std::move(work));
	}

	template<typename F, typename... Args>
	[[nodiscard]] auto enqueue_task(F&& f, Args&&... args) -> std::future<std::invoke_result_t<F, Args...>>
	{
		using task_return_type = std::invoke_result_t<F, Args...>;
		using task_type = std::packaged_task<task_return_type()>;

		auto task = std::make_shared<task_type>(std::bind(std::forward<F>(f), std::forward<Args>(args)...));
		auto work = [=]() { (*task)(); };
		auto result = task->get_future();
		auto i = m_index++;

		for(std::size_t n = 0; n < m_count * K; ++n)
			if(m_queues[(i + n) % m_count].try_push(work))
				return result;

		m_queues[i % m_count].push(std::move(work));

		return result;
	}

private:
	using proc_t = std::function<void(void)>;
	using queue_t = unbounded_queue<proc_t>;
	using queues_t = std::vector<queue_t>;
	queues_t m_queues;

	using threads_t = std::vector<std::thread>;
	threads_t m_threads;

	const std::size_t m_count;
	std::atomic_uint m_index = 0;

	inline static const unsigned int K = 2;
};
