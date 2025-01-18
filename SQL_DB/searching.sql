-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: finvision
-- ------------------------------------------------------
-- Server version	8.4.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `searching`
--

DROP TABLE IF EXISTS `searching`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `searching` (
  `id` int NOT NULL AUTO_INCREMENT,
  `terms` varchar(255) NOT NULL,
  `related_term` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  FULLTEXT KEY `ft_index` (`terms`,`related_term`),
  FULLTEXT KEY `terms` (`terms`,`related_term`)
) ENGINE=InnoDB AUTO_INCREMENT=222 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `searching`
--

LOCK TABLES `searching` WRITE;
/*!40000 ALTER TABLE `searching` DISABLE KEYS */;
INSERT INTO `searching` VALUES (1,'營業利益率','營利率'),(2,'營業利益率','營業利潤率'),(3,'營業利益率','Operating Profit Margin'),(4,'營業利益率','OPM'),(5,'營業現金流','現金流'),(6,'營業現金流','營運現金流'),(7,'營業現金流','Operating Cash Flow'),(8,'營業現金流','OCF'),(9,'營業收入','收入'),(10,'營業收入','營收'),(11,'營業收入','營業營收'),(12,'營業收入','Revenue'),(13,'營業收入','Sales Revenue'),(14,'營業收入','ZTT'),(15,'營業利益','利潤'),(16,'營業利益','營業利潤'),(17,'營業利益','Operating Income'),(18,'營業利益','Operating Profit'),(19,'營運周轉天數','周轉天數'),(20,'營運周轉天數','營運周期'),(21,'營運周轉天數','Operating Cycle Days'),(22,'營運周轉天數','Days of Operations'),(23,'營運周轉天數','OCD'),(24,'營收季成長率','成長率'),(25,'營收季成長率','季成長'),(26,'營收季成長率','Revenue Growth Rate'),(27,'營收季成長率','Quarterly Growth Rate'),(28,'營收季成長率','RGR_Q'),(29,'資產報酬率','ROA'),(30,'資產報酬率','Return on Assets'),(31,'資產報酬率','資產回報率'),(32,'資產周轉率','資產週轉'),(33,'資產周轉率','Total Asset Turnover'),(34,'資產周轉率','TAT'),(35,'資產總額季成長率','成長率'),(36,'資產總額季成長率','資產成長'),(37,'資產總額季成長率','Total Asset Growth Rate'),(38,'資產總額季成長率','TAGR'),(39,'資本支出','資本成本'),(40,'資本支出','資產投資'),(41,'資本支出','Capital Expenditure'),(42,'資本支出','CapEx'),(43,'資本支出','CAPEX'),(44,'資本公積','資本餘額'),(45,'資本公積','資本盈餘'),(46,'資本公積','Additional Paid-in Capital'),(47,'資本公積','Share Premium'),(48,'資本公積','XMZ'),(49,'應收帳款','應收款項'),(50,'應收帳款','應收債權'),(51,'應收帳款','Accounts Receivable'),(52,'應收帳款','AR'),(53,'應收帳款周轉率','應收周轉率'),(54,'應收帳款周轉率','AR Turnover'),(55,'應收帳款周轉率','Accounts Receivable Turnover Ratio'),(56,'應收帳款周轉率','ART'),(57,'應收帳款收現天數','收現天數'),(58,'應收帳款收現天數','應收款天數'),(59,'應收帳款收現天數','AR Collection Days'),(60,'應收帳款收現天數','Days Sales Outstanding'),(61,'應收帳款收現天數','DSO'),(62,'應付帳款','應付款項'),(63,'應付帳款','應付債權'),(64,'應付帳款','Accounts Payable'),(65,'應付帳款','AP'),(66,'稅後淨利','淨利'),(67,'稅後淨利','淨利潤'),(68,'稅後淨利','Profit After Tax'),(69,'稅後淨利','Net Income'),(70,'稅後淨利','PAT'),(71,'稅後淨利率','淨利潤率'),(72,'稅後淨利率','稅後利潤率'),(73,'稅後淨利率','Net Profit Margin '),(74,'稅後淨利率','After-Tax Profit Margin'),(75,'稅後淨利率','NPM'),(76,'稅後淨利季成長率','淨利成長率'),(77,'稅後淨利季成長率','季度利潤增長率'),(78,'稅後淨利季成長率','Net Profit Quarterly Growth Rate'),(79,'稅後淨利季成長率','HTO'),(80,'長期負債比率','長期債務率'),(81,'長期負債比率','長期債務占比'),(82,'長期負債比率','Long-Term Debt Ratio'),(83,'長期負債比率','Long-Term Liabilities Ratio'),(84,'長期負債比率','LTDR'),(85,'長期借款','長期貸款'),(86,'長期借款','長期負債'),(87,'長期借款','Long-Term Loans'),(88,'長期借款','Long-Term Borrowings'),(89,'長期借款','ZWG'),(90,'股東權益總額','股東權益'),(91,'股東權益總額','淨資產'),(92,'股東權益總額','Shareholders\' Equity'),(93,'股東權益總額','Total Equity'),(94,'股東權益總額','SEQ'),(95,'股東權益報酬率','股權回報率'),(96,'股東權益報酬率','淨資產收益率'),(97,'股東權益報酬率','ROE'),(98,'股東權益報酬率','Equity Return Rate'),(99,'股東權益報酬率','Return on Equity'),(100,'股本','普通股股本'),(101,'股本','資本總額'),(102,'股本','Capital Stock'),(103,'股本','Paid-in Capital'),(104,'股本','NMJ'),(105,'流動比率','短期償債能力'),(106,'流動比率','Current Ratio'),(107,'流動比率','流動性比率'),(108,'流動比率','CURR'),(109,'流動資產','短期資產'),(110,'流動資產','Current Assets'),(111,'流動資產','營運資產'),(112,'流動資產','BUP'),(113,'流動負債','短期負債'),(114,'流動負債','Current Liabilities'),(115,'流動負債','營運負債'),(116,'流動負債','BWO'),(117,'非流動資產','長期資產'),(118,'非流動資產','固定資產'),(119,'非流動資產','Non-Current Assets'),(120,'非流動資產','Long-Term Assets'),(121,'非流動資產','KQQ'),(122,'非流動負債','長期負債'),(123,'非流動負債','長期義務'),(124,'非流動負債','Non-Current Liabilities'),(125,'非流動負債','Long-Term Liabilities'),(126,'非流動負債','IAO'),(127,'存貨','庫存'),(128,'存貨','存貨資產'),(129,'存貨','Inventory'),(130,'存貨','Stock'),(131,'存貨','WZS'),(132,'存貨周轉率','庫存周轉率'),(133,'存貨周轉率','Inventory Turnover'),(134,'存貨周轉率','Stock Turnover'),(135,'存貨周轉率','IT'),(136,'存貨周轉天數','平均庫存天數'),(137,'存貨周轉天數','Inventory Days'),(138,'存貨周轉天數','Days Sales of Inventory '),(139,'存貨周轉天數','DSI'),(140,'負債比率','債務比率'),(141,'負債比率','負債占比'),(142,'負債比率','Debt Ratio'),(143,'負債比率','Liability Ratio'),(144,'負債比率','DR'),(145,'負債對淨值比率','負債權益比率'),(146,'負債對淨值比率','債務資本比率'),(147,'負債對淨值比率','Debt-to-Equity Ratio'),(148,'負債對淨值比率','負債股權比率'),(149,'負債對淨值比率','Debt-Equity Ratio'),(150,'負債對淨值比率','D/E Ratio'),(151,'負債對淨值比率','DER'),(152,'總資產','資產總額'),(153,'總資產','Total Assets'),(154,'總資產','總財務資產'),(155,'總資產','YRR'),(156,'總負債','負債總額'),(157,'總負債','Total Liabilities'),(158,'總負債','總債務'),(159,'總負債','VSD'),(160,'固定資產','長期資產'),(161,'固定資產','固定資本'),(162,'固定資產','Fixed Assets'),(163,'固定資產','Property, Plant, and Equipment '),(164,'固定資產','PPE'),(165,'毛利率','毛利率百分比'),(166,'毛利率','Gross Margin'),(167,'毛利率','Gross Profit Margin'),(168,'毛利率','GPM'),(169,'速動比率','酸性測試比率'),(170,'速動比率','Quick Ratio'),(171,'速動比率','Acid Test Ratio'),(172,'速動比率','QR'),(173,'現金比率','現金流動比率'),(174,'現金比率','Cash Ratio'),(175,'現金比率','現金償付比率'),(176,'現金比率','CR'),(177,'利息保障倍數','資息保障倍數'),(178,'利息保障倍數','Interest Coverage Ratio'),(179,'利息保障倍數','EBIT Interest Coverage'),(180,'利息保障倍數','ICR'),(181,'投資現金流','投資活動現金流'),(182,'投資現金流','Investment Cash Flow'),(183,'投資現金流','Investing Activities Cash Flow'),(184,'投資現金流','ICF'),(185,'融資現金流','融資活動現金流'),(186,'融資現金流','Financing Cash Flow'),(187,'融資現金流','Financing Activities Cash Flow'),(188,'融資現金流','FCF'),(189,'自由現金流','自由現金流量'),(190,'自由現金流','Free Cash Flow'),(191,'自由現金流','可支配現金流'),(192,'自由現金流','FCFREE'),(193,'淨現金流','現金流淨額'),(194,'淨現金流','Net Cash Flow'),(195,'淨現金流','現金流量'),(196,'淨現金流','NCF'),(197,'期末現金','現金期末餘額'),(198,'期末現金','Ending Cash Balance'),(199,'期末現金','Cash at End of Period'),(200,'期末現金','EOB'),(201,'無形資產','知識產權'),(202,'無形資產','Intangible Assets'),(203,'無形資產','Non-Physical Assets'),(204,'無形資產','XUF'),(205,'短期借款','短期貸款'),(206,'短期借款','Short-Term Loans'),(207,'短期借款','Short-Term Borrowing'),(208,'短期借款','PTP'),(209,'銷售收入','營業收入'),(210,'銷售收入','銷貨收入'),(211,'銷售收入','Sales Revenue'),(212,'銷售收入','Net Sales'),(213,'銷售收入','SHW'),(214,'保留盈餘','留存利潤'),(215,'保留盈餘','Retained Earnings'),(216,'保留盈餘','Accumulated Profit'),(217,'保留盈餘','KXL'),(218,'每股淨值','每股資產淨值'),(219,'每股淨值','Net Asset Value per Share'),(220,'每股淨值','Book Value Per Share (BVPS)'),(221,'每股淨值','CNX');
/*!40000 ALTER TABLE `searching` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-01-13 14:27:57
