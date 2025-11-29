package com.example.voicenotea.data

import kotlinx.coroutines.flow.Flow

interface MemoRepository {
    fun getAllMemos(): Flow<List<Memo>>
    suspend fun getMemoById(id: Long): Memo?
    suspend fun insertMemo(memo: Memo): Long
    suspend fun updateMemo(memo: Memo)
    suspend fun deleteMemoById(id: Long)
}

class MemoRepositoryImpl(private val memoDao: MemoDao) : MemoRepository {
    override fun getAllMemos(): Flow<List<Memo>> = memoDao.getAllMemos()

    override suspend fun getMemoById(id: Long): Memo? = memoDao.getMemoById(id)

    override suspend fun insertMemo(memo: Memo): Long = memoDao.insertMemo(memo)

    override suspend fun updateMemo(memo: Memo) = memoDao.updateMemo(memo)

    override suspend fun deleteMemoById(id: Long) = memoDao.deleteMemoById(id)
}
