import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {

  return <Main>
    <MetaTags>
      <title>Технологии</title>
      <meta name="description" content="Фудграм - Технологии" />
      <meta property="og:title" content="Технологии" />
    </MetaTags>

    <Container>
      <h1 className={styles.title}>Используемые инструменты</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Что лежит в основе проекта:</h2>
          <p className={styles.text}>
            Фудграм имеет современные и надежные технологии в основе, обеспечивая высокую производительность,
            и стабильность как для разработчиков, так и для пользователей.
          </p>
          <div className={styles.text}>
            <ul className={styles.textItem}>
              <li className={styles.textItem}>
                Django REST Framework — API, построенное в стиле REST, обеспечивает лёгкость интеграции и надёжное взаимодействие между клиентом и сервером.
              </li>
              <li className={styles.textItem}>
                PostgreSQL — высокопроизводительная и масштабируемая база данных для хранения информации о рецептах, избранном и списках покупок.
              </li>
              <li className={styles.textItem}>
                React — современный фреймворк для создания динамичного и отзывчивого интерфейса, обеспечивающий удобство использования.
              </li>
              <li className={styles.textItem}>
                Docker — инструмент для изоляции приложения, позволяющий запускать проект в стабильной и предсказуемой среде независимо от платформы.
              </li>
              <li className={styles.textItem}>
                Nginx и Gunicorn — серверная часть, которая обеспечивает быструю загрузку страниц и надёжную работу под нагрузкой.
              </li>
              <li className={styles.textItem}>
                GitHub Actions — автоматизированный процесс CI/CD, который тестирует код, собирает и развёртывает обновления, минимизируя вероятность ошибок.
              </li>
              <li className={styles.textItem}>
                Server Deployment — развёртывание проекта организовано с использованием современных подходов, что обеспечивает стабильный доступ и быструю работу сайта в продакшн-окружении.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Container>
  </Main>
}

export default Technologies