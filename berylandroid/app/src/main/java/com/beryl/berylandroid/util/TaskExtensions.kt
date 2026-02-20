package com.beryl.berylandroid.util

import com.google.android.gms.tasks.Task
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

suspend fun <T> Task<T>.awaitResult(): T = suspendCancellableCoroutine { cont ->
    addOnSuccessListener { result ->
        cont.resume(result)
    }.addOnFailureListener { exception ->
        cont.resumeWithException(exception)
    }
}
