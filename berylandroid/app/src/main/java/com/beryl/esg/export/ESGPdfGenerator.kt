package com.beryl.esg.export

import android.content.Context
import android.graphics.Paint
import android.graphics.pdf.PdfDocument
import java.io.File

class ESGPdfGenerator(private val context: Context) {

    fun generatePdf(record: ESGAuditRecord): File {
        val document = PdfDocument()
        val pageInfo = PdfDocument.PageInfo.Builder(595, 842, 1).create()
        val page = document.startPage(pageInfo)

        val canvas = page.canvas
        val paint = Paint()
        paint.textSize = 14f

        var y = 40

        fun drawLine(text: String) {
            canvas.drawText(text, 40f, y.toFloat(), paint)
            y += 25
        }

        drawLine("RAPPORT D’IMPACT ESG")
        y += 20
        drawLine("Ville : ${record.ville}")
        drawLine("Période : ${record.periode}")
        y += 10
        drawLine("Km verts : ${record.kmVerts}")
        drawLine("CO₂ évité : ${record.co2EviteKg} kg")
        y += 10
        drawLine("Score ESG : ${record.scoreEsg}")
        drawLine("Classe d’impact : ${record.classeImpact}")
        y += 20
        drawLine("Message IA AOQ :")
        y += 20

        record.messageAoq.chunked(60).forEach {
            drawLine(it)
        }

        y += 40
        drawLine("Document généré par le moteur ESG piloté par IA.")

        document.finishPage(page)

        val file = File(context.filesDir, "rapport_esg_${System.currentTimeMillis()}.pdf")
        document.writeTo(file.outputStream())
        document.close()

        return file
    }
}
