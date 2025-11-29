package com.example.voicenotea.data

import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test

class MemoRepositoryTest {
    private lateinit var memoDao: MemoDao
    private lateinit var repository: MemoRepository

    @Before
    fun setup() {
        memoDao = mockk()
        repository = MemoRepositoryImpl(memoDao)
    }

    @Test
    fun insertMemo_should_call_dao_insert_method() = runTest {
        val memo = Memo(
            title = "Test Memo",
            body = "Test content"
        )

        coEvery { memoDao.insertMemo(memo) } returns 1L

        val result = repository.insertMemo(memo)

        assertEquals(1L, result)
        coVerify { memoDao.insertMemo(memo) }
    }

    @Test
    fun updateMemo_should_call_dao_update_method() = runTest {
        val memo = Memo(
            id = 1,
            title = "Updated Title",
            body = "Updated content"
        )

        coEvery { memoDao.updateMemo(memo) } returns Unit

        repository.updateMemo(memo)

        coVerify { memoDao.updateMemo(memo) }
    }

    @Test
    fun deleteMemoById_should_call_dao_delete_method() = runTest {
        val memoId = 1L

        coEvery { memoDao.deleteMemoById(memoId) } returns Unit

        repository.deleteMemoById(memoId)

        coVerify { memoDao.deleteMemoById(memoId) }
    }

    @Test
    fun getMemoById_should_return_memo_from_dao() = runTest {
        val expectedMemo = Memo(
            id = 1,
            title = "Test",
            body = "Content"
        )

        coEvery { memoDao.getMemoById(1) } returns expectedMemo

        val result = repository.getMemoById(1)

        assertEquals(expectedMemo, result)
        coVerify { memoDao.getMemoById(1) }
    }
}
