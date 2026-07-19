package com.xenglish.data

import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.Streaming

interface XEnglishApi {

    @Multipart
    @POST("api/v1/analyze")
    suspend fun analyze(
        @Part audio: MultipartBody.Part,
        @Part("format") format: okhttp3.RequestBody,
    ): AnalyzeResponse

    @GET("api/v1/phrases")
    suspend fun listPhrases(
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0,
    ): PhraseListResponse

    @GET("api/v1/phrases/{id}")
    suspend fun getPhrase(@Path("id") id: String): AnalyzeResponse

    @Streaming
    @GET("api/v1/phrases/{id}/audio")
    suspend fun getPhraseAudio(
        @Path("id") id: String,
        @Query("variant") variant: String = "corrected",
    ): ResponseBody
}
